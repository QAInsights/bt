"""
BLE Packet Logger — timestamps and logs all BLE operations to file.

Usage:
    from packet_logger import PacketLogger

    logger = PacketLogger("AA:BB:CC:DD:EE:FF")
    logger.log_connect("AA:BB:CC:DD:EE:FF")
    logger.log_read("2a19", b'\\x64')
    logger.log_write("2a00", b'hello')
    logger.log_notify("2a37", b'\\x00\\x48')
    logger.log_disconnect()

Logs are saved to: ./logs/<address>_<timestamp>.log
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


LOG_DIR = Path("./logs")


class PacketLogger:
    """Logs all BLE operations with timestamps to a file."""

    def __init__(self, address: str, log_dir: Path = LOG_DIR):
        self.address = address.replace(":", "-")
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{self.address}_{ts}.log"
        self.json_file = self.log_dir / f"{self.address}_{ts}.json"

        self._entries = []
        self._file = open(self.log_file, "a", encoding="utf-8")

        self._write_header()

    def _write_header(self):
        header = (
            f"{'='*70}\n"
            f"  BLE Packet Log\n"
            f"  Device:  {self.address}\n"
            f"  Started: {datetime.now().isoformat()}\n"
            f"{'='*70}\n"
        )
        self._file.write(header)
        self._file.flush()

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _log(self, direction: str, op: str, detail: str, raw_data: bytes = None):
        ts = self._timestamp()
        line = f"[{ts}] {direction} {op:12s} | {detail}"
        self._file.write(line + "\n")
        self._file.flush()

        # Also store structured entry for JSON export
        entry = {
            "timestamp": datetime.now().isoformat(),
            "direction": direction,
            "operation": op,
            "detail": detail,
        }
        if raw_data is not None:
            entry["hex"] = raw_data.hex()
            entry["length"] = len(raw_data)
            # Try to decode as text
            try:
                entry["text"] = raw_data.decode("utf-8", errors="replace")
            except Exception:
                pass
        self._entries.append(entry)

        return line

    def log_connect(self, address: str) -> str:
        return self._log("-->", "CONNECT", f"Address: {address}")

    def log_disconnect(self) -> str:
        return self._log("<--", "DISCONNECT", f"Device: {self.address}")

    def log_scan(self, device_count: int) -> str:
        return self._log("...", "SCAN", f"Found {device_count} device(s)")

    def log_services(self, services: dict) -> str:
        svc_count = len(services)
        char_count = sum(len(s.get("characteristics", {})) for s in services.values())
        return self._log("<--", "SERVICES", f"{svc_count} services, {char_count} characteristics")

    def log_read(self, char_uuid: str, data: bytes) -> str:
        hex_str = data.hex() if data else "(empty)"
        try:
            text = data.decode("utf-8", errors="replace") if data else ""
        except Exception:
            text = ""
        detail = f"Char: {char_uuid}  Data[{len(data)}]: {hex_str}"
        if text and text.isprintable():
            detail += f"  ({text})"
        return self._log("<--", "READ", detail, data)

    def log_write(self, char_uuid: str, data: bytes) -> str:
        if isinstance(data, str):
            data = data.encode()
        hex_str = data.hex() if data else "(empty)"
        try:
            text = data.decode("utf-8", errors="replace") if data else ""
        except Exception:
            text = ""
        detail = f"Char: {char_uuid}  Data[{len(data)}]: {hex_str}"
        if text and text.isprintable():
            detail += f"  ({text})"
        return self._log("-->", "WRITE", detail, data)

    def log_notify(self, char_uuid: str, data: bytearray) -> str:
        hex_str = data.hex() if data else "(empty)"
        try:
            text = data.decode("utf-8", errors="replace") if data else ""
        except Exception:
            text = ""
        detail = f"Char: {char_uuid}  Data[{len(data)}]: {hex_str}"
        if text and text.isprintable():
            detail += f"  ({text})"
        return self._log("<==", "NOTIFY", detail, bytes(data))

    def log_error(self, operation: str, error: str) -> str:
        return self._log("!!", "ERROR", f"{operation}: {error}")

    def log_info(self, message: str) -> str:
        return self._log("   ", "INFO", message)

    def save_json(self):
        """Save structured log as JSON for programmatic analysis."""
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump({
                "device": self.address,
                "session_start": self._entries[0]["timestamp"] if self._entries else None,
                "session_end": datetime.now().isoformat(),
                "total_packets": len(self._entries),
                "packets": self._entries,
            }, f, indent=2)

    def get_summary(self) -> dict:
        """Get summary statistics of the session."""
        ops = {}
        for entry in self._entries:
            op = entry["operation"]
            ops[op] = ops.get(op, 0) + 1
        return {
            "total_packets": len(self._entries),
            "operations": ops,
            "log_file": str(self.log_file),
            "json_file": str(self.json_file),
        }

    def close(self):
        """Flush and close log files. Also saves JSON."""
        try:
            self.save_json()
        except Exception:
            pass
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
