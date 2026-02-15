import asyncio
from typing import Optional, Callable
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
import questionary

from ble import BleManager
from gatt_uuids import resolve_service, resolve_characteristic, resolve_uuid, format_uuid_with_name
from packet_logger import PacketLogger
from rssi_monitor import RSSIMonitor
from security_audit import BLESecurityAuditor, format_report_rich, export_report_json
from dashboard import start_dashboard

app = typer.Typer()
console = Console()
manager = BleManager()


async def run_interactive_session_async(address: str):
    """Main async session for read/write/listen operations."""
    logger = PacketLogger(address)
    console.print(f"[bold]Connecting to[/bold] {address}...")
    client = await manager.connect(address)
    logger.log_connect(address)
    console.print(":white_check_mark: [green]Connected[/green]\n")
    
    try:
        # Fetch and display device properties
        services = await manager.get_services(client)
        logger.log_services(services)
        
        # Display services and characteristics with resolved GATT names
        tree = Tree(f"[bold cyan]Device Properties[/bold cyan] ({address})")
        
        char_list = []
        for service_uuid, service_data in services.items():
            svc_name = resolve_service(service_uuid)
            svc_label = f"[bold magenta]Service:[/bold magenta] {service_uuid}"
            if svc_name != "Unknown Service":
                svc_label += f"  [bold white]({svc_name})[/bold white]"
            service_node = tree.add(svc_label)
            service_node.add(f"[dim]{service_data['description']}[/dim]")
            
            chars_node = service_node.add("[cyan]Characteristics:[/cyan]")
            for char_uuid, char_data in service_data["characteristics"].items():
                char_name = resolve_characteristic(char_uuid)
                props_str = ", ".join(char_data["properties"]) if char_data["properties"] else "none"
                char_label = f"[green]{char_uuid}[/green]"
                if char_name != "Unknown":
                    char_label += f"  [bold white]({char_name})[/bold white]"
                char_node = chars_node.add(char_label)
                char_node.add(f"[dim]{char_data['description']}[/dim]")
                char_node.add(f"[yellow]Properties:[/yellow] {props_str}")
                char_list.append((char_uuid, char_data["properties"]))
        
        console.print(tree)
        
        # Interactive menu
        while True:
            action = await questionary.select(
                "Choose an action:",
                choices=["Read Characteristic", "Write Characteristic", "Listen to Characteristic", "Disconnect"],
                use_indicator=True,
                use_arrow_keys=True
            ).ask_async()
            
            if action is None:  # Ctrl+C / cancelled
                break
            
            if action == "Read Characteristic":
                char_choices = [str(c[0]) for c in char_list if "read" in c[1]]
                if not char_choices:
                    console.print("[yellow]No readable characteristics[/yellow]")
                    continue
                char_uuid = await questionary.select(
                    "Select characteristic:",
                    choices=char_choices,
                    use_arrow_keys=True
                ).ask_async()
                if char_uuid is None:
                    continue
                try:
                    data = await manager.read_char(client, char_uuid)
                    logger.log_read(char_uuid, data)
                    console.print(f":white_check_mark: [green]Read:[/green] {data}")
                except Exception as e:
                    logger.log_error("READ", str(e))
                    console.print(f"[red]Read failed: {e}")
                    
            elif action == "Write Characteristic":
                char_choices = [str(c[0]) for c in char_list if "write" in c[1]]
                if not char_choices:
                    console.print("[yellow]No writable characteristics[/yellow]")
                    continue
                char_uuid = await questionary.select(
                    "Select characteristic:",
                    choices=char_choices,
                    use_arrow_keys=True
                ).ask_async()
                if char_uuid is None:
                    continue
                message = await questionary.text("Enter message to write:").ask_async()
                if message is None:
                    continue
                try:
                    await manager.write_char(client, char_uuid, message)
                    logger.log_write(char_uuid, message)
                    console.print(":white_check_mark: [green]Write successful[/green]")
                except Exception as e:
                    logger.log_error("WRITE", str(e))
                    console.print(f"[red]Write failed: {e}")
                    
            elif action == "Listen to Characteristic":
                char_choices = [str(c[0]) for c in char_list if "notify" in c[1] or "indicate" in c[1]]
                if not char_choices:
                    console.print("[yellow]No notifiable characteristics[/yellow]")
                    continue
                char_uuid = await questionary.select(
                    "Select characteristic:",
                    choices=char_choices,
                    use_arrow_keys=True
                ).ask_async()
                if char_uuid is None:
                    continue
                console.print(f"[cyan]Listening on {char_uuid}...[/cyan]")
                
                notify_count = 0
                stop_event = asyncio.Event()

                def _cb(sender, data: bytearray):
                    nonlocal notify_count
                    notify_count += 1
                    logger.log_notify(char_uuid, data)
                    try:
                        text = data.decode("utf-8", errors="replace")
                    except Exception:
                        text = ""
                    console.print(f"[blue]→[/blue] #{notify_count}  hex={data.hex()}  text={text}")

                def _wait_for_enter():
                    try:
                        input()
                    except EOFError:
                        pass
                    stop_event.set()
                
                try:
                    await client.start_notify(char_uuid, _cb)
                    console.print("[dim]Notifications started. Press Enter to stop.[/dim]")
                    
                    # Wait for Enter in a background thread
                    import threading
                    t = threading.Thread(target=_wait_for_enter, daemon=True)
                    t.start()
                    
                    # Keep the async loop alive while waiting
                    while not stop_event.is_set():
                        await asyncio.sleep(0.1)
                    
                    await client.stop_notify(char_uuid)
                    console.print(f"[yellow]Stopped. Received {notify_count} notification(s).[/yellow]")
                except Exception as e:
                    console.print(f"[red]Listen failed: {e}")
                    
            else:  # Disconnect
                break
    
    except (KeyboardInterrupt, asyncio.CancelledError):
        console.print("\n[yellow]Interrupted.[/yellow]")
    finally:
        # Always disconnect cleanly
        try:
            if client.is_connected:
                await client.disconnect()
                logger.log_disconnect()
                console.print(":white_check_mark: [yellow]Disconnected[/yellow]")
        except Exception:
            pass
        # Save and close logs
        summary = logger.get_summary()
        logger.close()
        console.print(f"[dim]📄 Log saved: {summary['log_file']}[/dim]")
        console.print(f"[dim]📄 JSON saved: {summary['json_file']}[/dim]")


@app.command()
def scan(timeout: float = 5.0):
    """Scan for Bluetooth devices and select one to connect."""
    console.print(f"[bold cyan]Scanning for devices ({timeout}s)...[/bold cyan]")
    devices = asyncio.run(manager.scan(timeout))
    
    if not devices:
        console.print("[yellow]No devices found[/yellow]")
        return
    
    # Create choices list
    choices = [f"{d.name or '<unknown>':<30} {d.address}" for d in devices]
    
    # Interactive selection with arrow keys
    selected = questionary.select(
        "Select a device to connect:",
        choices=choices,
        use_indicator=True,
        use_arrow_keys=True
    ).ask()
    
    if selected:
        idx = choices.index(selected)
        addr = devices[idx].address
        try:
            asyncio.run(run_interactive_session_async(addr))
        except KeyboardInterrupt:
            console.print("\n:white_check_mark: [yellow]Exited[/yellow]")

@app.command()
def connect(address: str):
    """Connect to a device by MAC/address."""
    try:
        asyncio.run(run_interactive_session_async(address))
    except KeyboardInterrupt:
        console.print("\n:white_check_mark: [yellow]Exited[/yellow]")

@app.command()
def write(address: str, char: str, message: str = typer.Argument(...)):
    """Write a message to a characteristic on a connected device."""
    console.print(f"Writing to {char} on {address}...")
    async def _write():
        client = await manager.connect(address)
        await manager.write_char(client, char, message)
        console.print(":white_check_mark: [green]Write successful[/green]")
        await client.disconnect()
    try:
        asyncio.run(_write())
    except Exception as e:
        console.print(f"[red]Write failed: {e}")

@app.command()
def listen(address: str, char: str):
    """Listen for notifications on a characteristic."""
    console.print(f"Listening on {char} of {address}. Press Ctrl+C to stop.")
    
    def _cb(sender, data: bytearray):
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = ""
        console.print(f"[blue]→[/blue] hex={data.hex()}  text={text}")
    
    async def _listen():
        client = await manager.connect(address)
        try:
            await client.start_notify(char, _cb)
            while True:
                await asyncio.sleep(1)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        finally:
            try:
                await client.stop_notify(char)
            except Exception:
                pass
            try:
                if client.is_connected:
                    await client.disconnect()
            except Exception:
                pass
            console.print(":white_check_mark: [yellow]Stopped & Disconnected[/yellow]")
    
    try:
        asyncio.run(_listen())
    except KeyboardInterrupt:
        console.print(":white_check_mark: [yellow]Stopped[/yellow]")

@app.command()
def waves(duration: float = 60.0):
    """Live RSSI signal monitor — visualize BLE signal waves in real-time."""
    console.print("[bold cyan]📶 Starting BLE Signal Monitor...[/bold cyan]")
    console.print("[dim]Scanning for BLE advertisements. Press Ctrl+C to stop.[/dim]\n")
    
    monitor = RSSIMonitor()
    try:
        asyncio.run(monitor.run(duration=duration))
    except KeyboardInterrupt:
        console.print(f"\n[yellow]Stopped. Tracked {len(monitor.devices)} device(s), {monitor.scan_count} packets.[/yellow]")

@app.command()
def audit(address: str = typer.Argument(None), export: bool = typer.Option(False, "--export", help="Export report to JSON")):
    """Run a security audit on a BLE device. Checks for vulnerabilities."""
    
    # If no address given, scan and let user pick
    if not address:
        console.print("[bold cyan]Scanning for devices to audit...[/bold cyan]")
        devices = asyncio.run(manager.scan(5.0))
        if not devices:
            console.print("[yellow]No devices found[/yellow]")
            return
        choices = [f"{d.name or '<unknown>':<30} {d.address}" for d in devices]
        selected = questionary.select(
            "Select a device to audit:",
            choices=choices,
            use_indicator=True,
            use_arrow_keys=True
        ).ask()
        if not selected:
            return
        idx = choices.index(selected)
        address = devices[idx].address
    
    console.print(f"\n[bold red]🔐 Starting BLE Security Audit[/bold red]")
    console.print(f"[bold]Target:[/bold] {address}")
    console.print(f"[dim]Scanning advertisements (3s)...[/dim]")
    
    auditor = BLESecurityAuditor()
    
    async def _audit():
        return await auditor.audit(address)
    
    try:
        report = asyncio.run(_audit())
    except Exception as e:
        console.print(f"[red]Audit failed: {e}[/red]")
        return
    
    # Display the report
    format_report_rich(report)
    
    # Export to JSON if requested
    if export:
        import json
        from pathlib import Path
        export_dir = Path("./logs")
        export_dir.mkdir(parents=True, exist_ok=True)
        filename = export_dir / f"audit_{address.replace(':', '-')}_{report.timestamp[:10]}.json"
        with open(filename, "w") as f:
            json.dump(export_report_json(report), f, indent=2)
        console.print(f"\n[dim]📄 Report exported: {filename}[/dim]")

@app.command()
def web(port: int = typer.Option(8080, "--port", "-p", help="Port for the web dashboard")):
    """Launch real-time web dashboard for BLE monitoring, auditing & exploration."""
    console.print(f"[bold cyan]\n  🌐 BLE Web Dashboard[/bold cyan]")
    console.print(f"  [dim]Open your browser at[/dim] [bold]http://localhost:{port}[/bold]")
    start_dashboard(port=port)

@app.command()
def version():
    """Show version information."""
    console.print("[bold cyan]BT v2026.0.1[/bold cyan]")
    console.print("A versatile Bluetooth Low Energy (BLE) exploration and security auditing tool.")
    show_author()

def show_author():
    console.print("\nCreated by [bold]NaveenKumar Namachivayam[/bold].")
    console.print("[dim]GitHub:https://github.com/qainsights/bt[/dim]")

def main():
    app()

if __name__ == "__main__":
    main()
