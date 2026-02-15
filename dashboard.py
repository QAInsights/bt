"""
BLE Web Dashboard — real-time web UI for BLE device monitoring.

Serves a single-page web app with WebSocket for live data:
  - Real-time device scanning with RSSI
  - Live packet log stream
  - Audit results viewer
  - Signal strength charts

Usage:
    from dashboard import start_dashboard
    start_dashboard(port=8080)
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Set

from aiohttp import web
from bleak import BleakScanner, BleakClient

from gatt_uuids import resolve_service, resolve_characteristic
from security_audit import BLESecurityAuditor, export_report_json


# ──────────────────────────────────────────────────────────────
#  Dashboard State
# ──────────────────────────────────────────────────────────────

class DashboardState:
    """Shared state for the dashboard."""
    
    def __init__(self):
        self.devices: Dict[str, dict] = {}  # address -> device info
        self.packets: list = []  # recent packets
        self.ws_clients: Set[web.WebSocketResponse] = set()
        self.scanning = False
        self.scanner = None
        self.scan_count = 0
        self.audit_results: dict = None
        self.connected_device: str = None
    
    async def broadcast(self, msg_type: str, data: dict):
        """Send a message to all connected WebSocket clients."""
        message = json.dumps({"type": msg_type, "data": data})
        dead = set()
        for ws in self.ws_clients:
            try:
                await ws.send_str(message)
            except Exception:
                dead.add(ws)
        self.ws_clients -= dead


state = DashboardState()


# ──────────────────────────────────────────────────────────────
#  BLE Scanner (background task)
# ──────────────────────────────────────────────────────────────

async def ble_scan_loop():
    """Continuous BLE scanning in the background."""
    
    def detection_callback(device, adv_data):
        address = device.address
        name = device.name or adv_data.local_name or "<unknown>"
        rssi = adv_data.rssi
        
        if address not in state.devices:
            state.devices[address] = {
                "address": address,
                "name": name,
                "rssi": rssi,
                "rssi_history": [],
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "service_uuids": [str(u) for u in (adv_data.service_uuids or [])],
                "manufacturer_data": bool(adv_data.manufacturer_data),
                "tx_power": adv_data.tx_power,
                "packets": 0,
            }
        
        dev = state.devices[address]
        if name != "<unknown>":
            dev["name"] = name
        dev["rssi"] = rssi
        dev["rssi_history"].append(rssi)
        if len(dev["rssi_history"]) > 60:
            dev["rssi_history"] = dev["rssi_history"][-60:]
        dev["last_seen"] = datetime.now().isoformat()
        dev["packets"] += 1
        state.scan_count += 1
    
    state.scanning = True
    state.scanner = BleakScanner(detection_callback=detection_callback)
    
    try:
        await state.scanner.start()
        while state.scanning:
            # Broadcast device updates every 500ms
            devices_list = sorted(
                state.devices.values(),
                key=lambda d: d["rssi"] or -999,
                reverse=True
            )
            await state.broadcast("devices", {
                "devices": devices_list[:30],
                "total": len(state.devices),
                "packets": state.scan_count,
            })
            await asyncio.sleep(0.5)
    finally:
        await state.scanner.stop()
        state.scanning = False


# ──────────────────────────────────────────────────────────────
#  HTTP Routes
# ──────────────────────────────────────────────────────────────

async def handle_index(request):
    """Serve the dashboard HTML."""
    html_path = Path(__file__).parent / "static" / "dashboard.html"
    return web.FileResponse(html_path)


async def handle_api_devices(request):
    """Get current device list."""
    devices = sorted(
        state.devices.values(),
        key=lambda d: d["rssi"] or -999,
        reverse=True
    )
    return web.json_response({"devices": devices, "total": len(state.devices)})


async def handle_api_audit(request):
    """Run a security audit on a device."""
    data = await request.json()
    address = data.get("address")
    if not address:
        return web.json_response({"error": "address required"}, status=400)
    
    await state.broadcast("audit_status", {"status": "running", "address": address})
    
    try:
        auditor = BLESecurityAuditor()
        report = await auditor.audit(address)
        result = export_report_json(report)
        state.audit_results = result
        
        await state.broadcast("audit_result", result)
        return web.json_response(result)
    except Exception as e:
        error = {"error": str(e)}
        await state.broadcast("audit_status", {"status": "error", "error": str(e)})
        return web.json_response(error, status=500)


async def handle_api_connect(request):
    """Connect to a device and get its GATT services."""
    data = await request.json()
    address = data.get("address")
    if not address:
        return web.json_response({"error": "address required"}, status=400)
    
    try:
        client = BleakClient(address, timeout=10)
        await client.connect()
        
        services_data = {}
        for service in client.services:
            svc_name = resolve_service(service.uuid)
            chars = {}
            for char in service.characteristics:
                char_name = resolve_characteristic(char.uuid)
                
                # Try to read if readable
                value = None
                if "read" in char.properties:
                    try:
                        raw = await client.read_gatt_char(char.uuid)
                        try:
                            value = raw.decode("utf-8", errors="replace")
                        except Exception:
                            value = raw.hex()
                    except Exception:
                        value = "(read failed)"
                
                chars[char.uuid] = {
                    "uuid": char.uuid,
                    "name": char_name,
                    "properties": char.properties,
                    "value": value,
                }
            
            services_data[service.uuid] = {
                "uuid": service.uuid,
                "name": svc_name,
                "characteristics": chars,
            }
        
        await client.disconnect()
        
        return web.json_response({
            "address": address,
            "services": services_data,
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_api_logs(request):
    """Get available log files."""
    log_dir = Path("./logs")
    if not log_dir.exists():
        return web.json_response({"logs": []})
    
    logs = []
    for f in sorted(log_dir.glob("*.json"), reverse=True):
        try:
            with open(f) as fh:
                data = json.load(fh)
            logs.append({
                "filename": f.name,
                "device": data.get("device", {}),
                "timestamp": data.get("timestamp") or data.get("session_start"),
                "packets": data.get("total_packets", 0),
                "type": "audit" if f.name.startswith("audit_") else "session",
            })
        except Exception:
            pass
    
    return web.json_response({"logs": logs})


async def handle_api_log_detail(request):
    """Get a specific log file content."""
    filename = request.match_info["filename"]
    log_path = Path("./logs") / filename
    if not log_path.exists():
        return web.json_response({"error": "not found"}, status=404)
    
    try:
        with open(log_path) as f:
            data = json.load(f)
        return web.json_response(data)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# ──────────────────────────────────────────────────────────────
#  WebSocket Handler
# ──────────────────────────────────────────────────────────────

async def handle_ws(request):
    """WebSocket endpoint for real-time data."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    state.ws_clients.add(ws)
    
    # Send initial state
    await ws.send_str(json.dumps({
        "type": "init",
        "data": {
            "scanning": state.scanning,
            "device_count": len(state.devices),
            "packet_count": state.scan_count,
        }
    }))
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    cmd = data.get("cmd")
                    
                    if cmd == "clear_devices":
                        state.devices.clear()
                        state.scan_count = 0
                        
                except json.JSONDecodeError:
                    pass
            elif msg.type == web.WSMsgType.ERROR:
                break
    finally:
        state.ws_clients.discard(ws)
    
    return ws


# ──────────────────────────────────────────────────────────────
#  App Setup
# ──────────────────────────────────────────────────────────────

def create_app() -> web.Application:
    app = web.Application()
    
    app.router.add_get("/", handle_index)
    app.router.add_get("/ws", handle_ws)
    app.router.add_get("/api/devices", handle_api_devices)
    app.router.add_post("/api/audit", handle_api_audit)
    app.router.add_post("/api/connect", handle_api_connect)
    app.router.add_get("/api/logs", handle_api_logs)
    app.router.add_get("/api/logs/{filename}", handle_api_log_detail)
    
    return app


async def start_dashboard_async(host: str = "0.0.0.0", port: int = 8080):
    """Start the dashboard with BLE scanning."""
    app = create_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    print(f"\n  🌐 BLE Dashboard running at http://localhost:{port}")
    print(f"  📡 BLE scanning active...")
    print(f"  Press Ctrl+C to stop.\n")
    
    # Run BLE scanner in background
    scan_task = asyncio.create_task(ble_scan_loop())
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        state.scanning = False
        scan_task.cancel()
        try:
            await scan_task
        except asyncio.CancelledError:
            pass
        await runner.cleanup()


def start_dashboard(host: str = "0.0.0.0", port: int = 8080):
    """Start the dashboard (blocking)."""
    try:
        asyncio.run(start_dashboard_async(host, port))
    except KeyboardInterrupt:
        print("\n  Dashboard stopped.")
