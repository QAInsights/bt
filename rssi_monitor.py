"""
BLE RSSI Wave Monitor — real-time signal strength visualization in the terminal.

Usage:
    from rssi_monitor import RSSIMonitor

    monitor = RSSIMonitor()
    await monitor.run(duration=30.0)
"""

import asyncio
from collections import deque
from datetime import datetime
from typing import Dict, Optional
from bleak import BleakScanner
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout


# RSSI visualization constants
WAVE_WIDTH = 40          # characters wide for the wave display
HISTORY_SIZE = 40        # number of RSSI samples to keep per device
RSSI_MIN = -100          # weakest signal (dBm)
RSSI_MAX = -30           # strongest signal (dBm)

# Signal quality thresholds
SIGNAL_EXCELLENT = -50
SIGNAL_GOOD = -65
SIGNAL_FAIR = -80
SIGNAL_WEAK = -90


def rssi_to_bar(rssi: int, width: int = WAVE_WIDTH) -> Text:
    """Convert RSSI value to a colored bar with wave character."""
    if rssi is None:
        return Text("?" * 3, style="dim")
    
    # Normalize RSSI to 0-1 range
    normalized = max(0.0, min(1.0, (rssi - RSSI_MIN) / (RSSI_MAX - RSSI_MIN)))
    filled = int(normalized * width)
    
    # Color based on signal quality
    if rssi >= SIGNAL_EXCELLENT:
        color = "bright_green"
        label = "EXCELLENT"
    elif rssi >= SIGNAL_GOOD:
        color = "green"
        label = "GOOD"
    elif rssi >= SIGNAL_FAIR:
        color = "yellow"
        label = "FAIR"
    elif rssi >= SIGNAL_WEAK:
        color = "red"
        label = "WEAK"
    else:
        color = "bright_red"
        label = "VERY WEAK"
    
    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * (width - filled), style="dim")
    bar.append(f" {rssi}dBm ", style=f"bold {color}")
    bar.append(f"[{label}]", style=f"dim {color}")
    return bar


def rssi_to_wave(history: deque, width: int = WAVE_WIDTH) -> Text:
    """Convert RSSI history to a wave visualization."""
    if not history:
        return Text("~" * width, style="dim")
    
    wave = Text()
    # Take last `width` samples
    samples = list(history)[-width:]
    
    for rssi in samples:
        # Normalize to wave characters
        normalized = max(0.0, min(1.0, (rssi - RSSI_MIN) / (RSSI_MAX - RSSI_MIN)))
        
        # Choose wave character based on signal level
        if normalized > 0.8:
            char = "▇"
            color = "bright_green"
        elif normalized > 0.6:
            char = "▆"
            color = "green"
        elif normalized > 0.4:
            char = "▄"
            color = "yellow"
        elif normalized > 0.2:
            char = "▂"
            color = "red"
        else:
            char = "▁"
            color = "bright_red"
        
        wave.append(char, style=color)
    
    # Pad remaining width
    remaining = width - len(samples)
    if remaining > 0:
        wave.append("·" * remaining, style="dim")
    
    return wave


class DeviceTracker:
    """Tracks RSSI history for a single device."""
    
    def __init__(self, name: str, address: str):
        self.name = name or "<unknown>"
        self.address = address
        self.rssi_history: deque = deque(maxlen=HISTORY_SIZE)
        self.last_seen = datetime.now()
        self.first_seen = datetime.now()
        self.update_count = 0
    
    def update(self, rssi: int):
        self.rssi_history.append(rssi)
        self.last_seen = datetime.now()
        self.update_count += 1
    
    @property
    def current_rssi(self) -> Optional[int]:
        return self.rssi_history[-1] if self.rssi_history else None
    
    @property
    def avg_rssi(self) -> Optional[float]:
        if not self.rssi_history:
            return None
        return sum(self.rssi_history) / len(self.rssi_history)
    
    @property
    def min_rssi(self) -> Optional[int]:
        return min(self.rssi_history) if self.rssi_history else None
    
    @property
    def max_rssi(self) -> Optional[int]:
        return max(self.rssi_history) if self.rssi_history else None
    
    @property
    def age_seconds(self) -> float:
        return (datetime.now() - self.last_seen).total_seconds()


class RSSIMonitor:
    """Real-time BLE RSSI monitor with wave visualization."""
    
    def __init__(self):
        self.devices: Dict[str, DeviceTracker] = {}
        self.console = Console()
        self.scan_count = 0
        self.start_time = None
    
    def _detection_callback(self, device, advertisement_data):
        """Called for each BLE advertisement detected."""
        address = device.address
        rssi = advertisement_data.rssi
        name = device.name or advertisement_data.local_name
        
        if address not in self.devices:
            self.devices[address] = DeviceTracker(name, address)
        
        tracker = self.devices[address]
        if name and tracker.name == "<unknown>":
            tracker.name = name
        tracker.update(rssi)
        self.scan_count += 1
    
    def _build_display(self, show_waves: bool = True, top_n: int = 15) -> Panel:
        """Build the Rich display panel."""
        # Sort devices by current RSSI (strongest first)
        sorted_devices = sorted(
            self.devices.values(),
            key=lambda d: d.current_rssi or -999,
            reverse=True
        )[:top_n]
        
        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
            expand=True,
            pad_edge=False,
        )
        
        table.add_column("Device", style="white", min_width=18, max_width=22)
        table.add_column("Address", style="dim", min_width=17, max_width=17)
        
        if show_waves:
            table.add_column("Signal Wave", min_width=WAVE_WIDTH, max_width=WAVE_WIDTH + 2)
        
        table.add_column("RSSI", justify="right", min_width=12)
        table.add_column("Avg", justify="right", style="dim", min_width=7)
        table.add_column("Pkts", justify="right", style="dim", min_width=5)
        
        for tracker in sorted_devices:
            rssi = tracker.current_rssi
            avg = tracker.avg_rssi
            
            # Name with truncation
            name = tracker.name[:20] if tracker.name else "<unknown>"
            
            # Dim devices not seen recently
            age = tracker.age_seconds
            name_style = "bold white" if age < 5 else ("dim" if age > 15 else "white")
            
            row = [
                Text(name, style=name_style),
                Text(tracker.address),
            ]
            
            if show_waves:
                row.append(rssi_to_wave(tracker.rssi_history))
            
            row.append(rssi_to_bar(rssi, width=10) if rssi else Text("--", style="dim"))
            row.append(Text(f"{avg:.0f}" if avg else "--", style="dim"))
            row.append(Text(str(tracker.update_count), style="dim"))
            
            table.add_row(*row)
        
        # Build footer
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        footer = (
            f"  📡 {len(self.devices)} devices  |"
            f"  📦 {self.scan_count} packets  |"
            f"  ⏱ {elapsed:.0f}s  |"
            f"  Press Ctrl+C to stop"
        )
        
        return Panel(
            table,
            title="[bold cyan]📶 BLE Signal Monitor[/bold cyan]",
            subtitle=f"[dim]{footer}[/dim]",
            border_style="cyan",
        )
    
    async def run(self, duration: float = 60.0, update_interval: float = 0.5):
        """Run the RSSI monitor with live display."""
        self.start_time = datetime.now()
        
        scanner = BleakScanner(detection_callback=self._detection_callback)
        
        await scanner.start()
        
        try:
            with Live(self._build_display(), console=self.console, refresh_per_second=4) as live:
                end_time = asyncio.get_event_loop().time() + duration
                while asyncio.get_event_loop().time() < end_time:
                    await asyncio.sleep(update_interval)
                    live.update(self._build_display())
        finally:
            await scanner.stop()
