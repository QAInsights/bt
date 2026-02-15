"""
BLE Security Auditor — automated security assessment for BLE devices.

Connects to a device, enumerates all services/characteristics,
and checks for common BLE security issues.

Usage:
    from security_audit import BLESecurityAuditor
    auditor = BLESecurityAuditor()
    report = await auditor.audit("AA:BB:CC:DD:EE:FF")
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from gatt_uuids import (
    resolve_service, resolve_characteristic,
    SERVICES, CHARACTERISTICS, VENDOR_SERVICES,
    _extract_short_uuid,
)


# ──────────────────────────────────────────────────────────────────
#  Security Finding Definitions
# ──────────────────────────────────────────────────────────────────

class Severity:
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

SEVERITY_SCORES = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 5,
}

SEVERITY_ICONS = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH: "🟠",
    Severity.MEDIUM: "🟡",
    Severity.LOW: "🔵",
    Severity.INFO: "⚪",
}


@dataclass
class Finding:
    """A single security finding."""
    severity: str
    title: str
    description: str
    characteristic: str = ""
    service: str = ""
    recommendation: str = ""
    data: str = ""


@dataclass
class AuditReport:
    """Complete security audit report."""
    device_address: str
    device_name: str
    timestamp: str = ""
    connection_no_auth: bool = False
    total_services: int = 0
    total_characteristics: int = 0
    readable_chars: int = 0
    writable_chars: int = 0
    notify_chars: int = 0
    findings: List[Finding] = field(default_factory=list)
    exposed_data: Dict[str, str] = field(default_factory=dict)
    score: int = 10  # starts at 10, deductions applied
    grade: str = "A+"
    
    def add_finding(self, finding: Finding):
        self.findings.append(finding)
        # Deduct score based on severity
        deduction = {
            Severity.CRITICAL: 3,
            Severity.HIGH: 2,
            Severity.MEDIUM: 1,
            Severity.LOW: 0.5,
            Severity.INFO: 0,
        }.get(finding.severity, 0)
        self.score = max(0, self.score - deduction)
    
    def calculate_grade(self):
        if self.score >= 9:
            self.grade = "A+"
        elif self.score >= 8:
            self.grade = "A"
        elif self.score >= 7:
            self.grade = "B+"
        elif self.score >= 6:
            self.grade = "B"
        elif self.score >= 5:
            self.grade = "C"
        elif self.score >= 4:
            self.grade = "D"
        else:
            self.grade = "F"


# Sensitive characteristic UUIDs that shouldn't be freely readable
SENSITIVE_CHARS = {
    "2a00": "Device Name",
    "2a24": "Model Number",
    "2a25": "Serial Number",
    "2a26": "Firmware Revision",
    "2a27": "Hardware Revision",
    "2a28": "Software Revision",
    "2a29": "Manufacturer Name",
    "2a23": "System ID",
    "2a50": "PnP ID",
    "2a4a": "HID Information",
    "2a4b": "Report Map",
}

# Services that expose device info
DEVICE_INFO_SERVICE = "180a"
HID_SERVICE = "1812"


class BLESecurityAuditor:
    """Performs security audit on a BLE device."""

    async def audit(self, address: str, timeout: float = 10.0) -> AuditReport:
        """Run a full security audit on a BLE device."""
        report = AuditReport(
            device_address=address,
            device_name="Unknown",
            timestamp=datetime.now().isoformat(),
        )

        # ── Phase 1: Pre-connection scan ──
        await self._scan_advertisements(address, report)

        # ── Phase 2: Connection attempt (no pairing) ──
        client = BleakClient(address, timeout=timeout)
        
        try:
            await client.connect()
        except Exception as e:
            report.add_finding(Finding(
                severity=Severity.INFO,
                title="Connection Requires Authentication",
                description=f"Device refused unauthenticated connection: {e}",
                recommendation="This is good — the device requires pairing/authentication.",
            ))
            report.calculate_grade()
            return report

        # Connected without pairing = finding
        report.connection_no_auth = True
        report.add_finding(Finding(
            severity=Severity.MEDIUM,
            title="No Authentication Required",
            description="Device accepted connection without pairing or bonding.",
            recommendation="Implement BLE pairing with MITM protection (Secure Connections).",
        ))

        try:
            # ── Phase 3: Service enumeration ──
            await self._enumerate_services(client, report)

            # ── Phase 4: Read exposed data ──
            await self._probe_readable_chars(client, report)

            # ── Phase 5: Check write permissions ──
            await self._check_write_permissions(client, report)

            # ── Phase 6: Analyze service-level risks ──
            self._analyze_services(client, report)

            # ── Phase 7: Check notification security ──
            self._check_notification_security(client, report)

        finally:
            try:
                if client.is_connected:
                    await client.disconnect()
            except Exception:
                pass

        report.calculate_grade()
        return report

    async def _scan_advertisements(self, address: str, report: AuditReport):
        """Scan for the device's advertisement data."""
        target_address = address.upper()
        found = {"done": False}
        
        def _detection_cb(device, adv_data):
            if device.address.upper() != target_address:
                return
            
            # Always update device name
            if device.name:
                report.device_name = device.name
            
            # Only record advertisement findings once
            if found["done"]:
                return
            found["done"] = True
                    
            # Check if device is advertising services
            if adv_data.service_uuids:
                report.add_finding(Finding(
                    severity=Severity.LOW,
                    title="Services Advertised in Broadcast",
                    description=f"Device broadcasts {len(adv_data.service_uuids)} service UUID(s) publicly: "
                                + ", ".join(adv_data.service_uuids),
                    recommendation="Only advertise necessary service UUIDs to reduce attack surface.",
                ))
            
            # Check TX power
            if adv_data.tx_power is not None:
                if adv_data.tx_power > 4:
                    report.add_finding(Finding(
                        severity=Severity.LOW,
                        title=f"High TX Power ({adv_data.tx_power} dBm)",
                        description="Device is broadcasting at high power, increasing range of potential attacks.",
                        recommendation="Reduce TX power if device only needs short-range communication.",
                    ))
                    
            # Check manufacturer data
            if adv_data.manufacturer_data:
                report.add_finding(Finding(
                    severity=Severity.INFO,
                    title="Manufacturer Data in Advertisement",
                    description=f"Device broadcasts manufacturer-specific data for "
                                f"{len(adv_data.manufacturer_data)} company ID(s).",
                    recommendation="Ensure manufacturer data doesn't leak sensitive information.",
                ))

        scanner = BleakScanner(detection_callback=_detection_cb)
        await scanner.start()
        await asyncio.sleep(3)
        await scanner.stop()

    async def _enumerate_services(self, client: BleakClient, report: AuditReport):
        """Enumerate all services and characteristics."""
        services = client.services
        
        for service in services:
            report.total_services += 1
            for char in service.characteristics:
                report.total_characteristics += 1
                props = char.properties
                
                if "read" in props:
                    report.readable_chars += 1
                if "write" in props or "write-without-response" in props:
                    report.writable_chars += 1
                if "notify" in props or "indicate" in props:
                    report.notify_chars += 1

    async def _probe_readable_chars(self, client: BleakClient, report: AuditReport):
        """Try to read all readable characteristics and check for sensitive data."""
        services = client.services
        
        for service in services:
            for char in service.characteristics:
                if "read" not in char.properties:
                    continue
                
                try:
                    data = await client.read_gatt_char(char.uuid)
                    
                    # Try to decode as text
                    try:
                        text = data.decode("utf-8", errors="replace").strip()
                    except Exception:
                        text = data.hex()
                    
                    # Store exposed data
                    char_name = resolve_characteristic(char.uuid)
                    if char_name != "Unknown":
                        report.exposed_data[char_name] = text
                    else:
                        report.exposed_data[char.uuid] = text
                    
                    # Check if this is a sensitive characteristic
                    short_uuid = _extract_short_uuid(char.uuid)
                    if short_uuid and short_uuid in SENSITIVE_CHARS:
                        field_name = SENSITIVE_CHARS[short_uuid]
                        report.add_finding(Finding(
                            severity=Severity.MEDIUM,
                            title=f"Sensitive Data Readable: {field_name}",
                            description=f"'{field_name}' is readable without authentication. Value: '{text}'",
                            characteristic=char.uuid,
                            service=service.uuid,
                            recommendation=f"Protect '{field_name}' with encryption or authentication.",
                            data=text,
                        ))
                        
                except Exception:
                    pass  # Can't read — that's actually fine from security perspective

    async def _check_write_permissions(self, client: BleakClient, report: AuditReport):
        """Check for writable characteristics that could be dangerous."""
        services = client.services
        open_writes = []
        
        for service in services:
            svc_name = resolve_service(service.uuid)
            for char in service.characteristics:
                char_name = resolve_characteristic(char.uuid)
                
                if "write-without-response" in char.properties:
                    open_writes.append((char.uuid, char_name, service.uuid, svc_name))
                    report.add_finding(Finding(
                        severity=Severity.HIGH,
                        title=f"Write-Without-Response Enabled",
                        description=f"Characteristic '{char_name}' ({char.uuid}) allows "
                                    f"write-without-response. An attacker can send data without "
                                    f"any acknowledgment or pairing.",
                        characteristic=char.uuid,
                        service=service.uuid,
                        recommendation="Require pairing and use 'write' instead of "
                                       "'write-without-response' for sensitive commands.",
                    ))
                elif "write" in char.properties:
                    open_writes.append((char.uuid, char_name, service.uuid, svc_name))
        
        if open_writes:
            report.add_finding(Finding(
                severity=Severity.MEDIUM,
                title=f"{len(open_writes)} Writable Characteristic(s) Without Auth",
                description="These characteristics accept writes without authentication: "
                            + ", ".join(f"{name} ({uuid[:8]}...)" for uuid, name, _, _ in open_writes),
                recommendation="Implement write permissions that require bonding or encryption.",
            ))

    def _analyze_services(self, client: BleakClient, report: AuditReport):
        """Analyze service-level security concerns."""
        services = client.services
        
        for service in services:
            short_uuid = _extract_short_uuid(service.uuid)
            
            # Device Information Service exposed
            if short_uuid == DEVICE_INFO_SERVICE:
                report.add_finding(Finding(
                    severity=Severity.MEDIUM,
                    title="Device Information Service Exposed",
                    description="The Device Information Service (0x180A) is accessible without "
                                "authentication, potentially leaking manufacturer, model, serial "
                                "number, and firmware version.",
                    service=service.uuid,
                    recommendation="Restrict Device Information Service access or remove "
                                   "unnecessary characteristics.",
                ))
            
            # HID service exposed (keyboard/mouse emulation)
            if short_uuid == HID_SERVICE:
                report.add_finding(Finding(
                    severity=Severity.CRITICAL,
                    title="HID Service Exposed Without Auth",
                    description="Human Interface Device (HID) service is accessible. An attacker "
                                "could potentially inject keystrokes or mouse movements.",
                    service=service.uuid,
                    recommendation="HID service MUST require bonding with MITM protection.",
                ))
            
            # Generic Access service — check if device name is writable
            if short_uuid == "1800":
                for char in service.characteristics:
                    char_short = _extract_short_uuid(char.uuid)
                    if char_short == "2a00" and "write" in char.properties:
                        report.add_finding(Finding(
                            severity=Severity.HIGH,
                            title="Device Name is Writable",
                            description="Attacker can change the device name, enabling "
                                        "spoofing/impersonation attacks.",
                            characteristic=char.uuid,
                            recommendation="Make Device Name read-only or require authentication.",
                        ))

    def _check_notification_security(self, client: BleakClient, report: AuditReport):
        """Check notification/indication security."""
        services = client.services
        unsecured_notifs = []
        
        for service in services:
            for char in service.characteristics:
                if "notify" in char.properties or "indicate" in char.properties:
                    # Check if the characteristic has a CCCD descriptor
                    has_cccd = False
                    for desc in char.descriptors:
                        if _extract_short_uuid(desc.uuid) == "2902":
                            has_cccd = True
                            break
                    
                    if not has_cccd:
                        char_name = resolve_characteristic(char.uuid)
                        unsecured_notifs.append(f"{char_name} ({char.uuid[:8]}...)")
                        
        # Check for any notifiable characteristics (data exposure)
        services = client.services
        notify_count = 0
        for service in services:
            for char in service.characteristics:
                if "notify" in char.properties:
                    notify_count += 1
        
        if notify_count > 0:
            report.add_finding(Finding(
                severity=Severity.LOW,
                title=f"{notify_count} Notification Characteristic(s) Available",
                description="Any connected client can subscribe to notifications and "
                            "receive data stream without additional authorization.",
                recommendation="Ensure notification data doesn't contain sensitive information, "
                               "or require bonding before allowing subscriptions.",
            ))


def format_report_rich(report: AuditReport) -> str:
    """Format the report for Rich console output. Returns the raw text for the panel."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    from rich.text import Text
    
    console = Console()
    
    # Header
    grade_colors = {
        "A+": "bright_green", "A": "green", "B+": "cyan", 
        "B": "blue", "C": "yellow", "D": "red", "F": "bright_red",
    }
    grade_color = grade_colors.get(report.grade, "white")
    
    console.print()
    console.print(Panel(
        f"[bold]BLE Security Audit Report[/bold]\n"
        f"[dim]{'─' * 40}[/dim]\n"
        f"  Device:  [bold]{report.device_name}[/bold] ({report.device_address})\n"
        f"  Time:    {report.timestamp}\n"
        f"  Auth:    {'[red]No authentication required[/red]' if report.connection_no_auth else '[green]Authentication required[/green]'}\n"
        f"[dim]{'─' * 40}[/dim]\n"
        f"  Services:        {report.total_services}\n"
        f"  Characteristics: {report.total_characteristics}\n"
        f"    Readable:  {report.readable_chars}\n"
        f"    Writable:  {report.writable_chars}\n"
        f"    Notify:    {report.notify_chars}\n",
        title="[bold cyan]🔐 Security Audit[/bold cyan]",
        border_style="cyan",
    ))
    
    # Score
    console.print(Panel(
        f"[bold {grade_color}]   Score: {report.score:.1f}/10   Grade: {report.grade}   [/bold {grade_color}]",
        title="[bold]Security Score[/bold]",
        border_style=grade_color,
    ))
    
    # Findings
    if report.findings:
        # Group by severity
        severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
        
        findings_table = Table(
            show_header=True,
            header_style="bold",
            border_style="dim",
            expand=True,
        )
        findings_table.add_column("", width=2)
        findings_table.add_column("Severity", style="bold", width=10)
        findings_table.add_column("Finding", min_width=30)
        findings_table.add_column("Recommendation", min_width=25, style="dim")
        
        for severity in severity_order:
            sev_findings = [f for f in report.findings if f.severity == severity]
            for f in sev_findings:
                sev_colors = {
                    Severity.CRITICAL: "bright_red",
                    Severity.HIGH: "red",
                    Severity.MEDIUM: "yellow",
                    Severity.LOW: "cyan",
                    Severity.INFO: "dim",
                }
                color = sev_colors.get(f.severity, "white")
                findings_table.add_row(
                    SEVERITY_ICONS.get(f.severity, "?"),
                    Text(f.severity, style=color),
                    f"[bold]{f.title}[/bold]\n[dim]{f.description}[/dim]",
                    f.recommendation or "",
                )
        
        console.print(Panel(
            findings_table,
            title=f"[bold]Findings ({len(report.findings)})[/bold]",
            border_style="yellow",
        ))
    
    # Exposed Data
    if report.exposed_data:
        data_table = Table(
            show_header=True,
            header_style="bold",
            border_style="dim",
        )
        data_table.add_column("Field", style="cyan", min_width=25)
        data_table.add_column("Exposed Value", style="white")
        
        for field_name, value in report.exposed_data.items():
            # Truncate long values
            display_val = value[:80] + "..." if len(value) > 80 else value
            # Check if it's printable
            if not display_val.isprintable():
                display_val = f"[hex] {value.encode().hex()}" if isinstance(value, str) else value
            data_table.add_row(field_name, display_val)
        
        console.print(Panel(
            data_table,
            title="[bold]📋 Exposed Data (readable without auth)[/bold]",
            border_style="red",
        ))
    
    # Summary
    crit = len([f for f in report.findings if f.severity == Severity.CRITICAL])
    high = len([f for f in report.findings if f.severity == Severity.HIGH])
    med = len([f for f in report.findings if f.severity == Severity.MEDIUM])
    low = len([f for f in report.findings if f.severity == Severity.LOW])
    info = len([f for f in report.findings if f.severity == Severity.INFO])
    
    console.print(
        f"\n  🔴 Critical: {crit}  🟠 High: {high}  "
        f"🟡 Medium: {med}  🔵 Low: {low}  ⚪ Info: {info}\n"
    )


def export_report_json(report: AuditReport) -> dict:
    """Export the report as a JSON-serializable dict."""
    return {
        "device": {
            "address": report.device_address,
            "name": report.device_name,
        },
        "timestamp": report.timestamp,
        "score": round(report.score, 1),
        "grade": report.grade,
        "connection_no_auth": report.connection_no_auth,
        "stats": {
            "total_services": report.total_services,
            "total_characteristics": report.total_characteristics,
            "readable": report.readable_chars,
            "writable": report.writable_chars,
            "notify": report.notify_chars,
        },
        "findings": [
            {
                "severity": f.severity,
                "title": f.title,
                "description": f.description,
                "characteristic": f.characteristic,
                "service": f.service,
                "recommendation": f.recommendation,
                "data": f.data,
            }
            for f in report.findings
        ],
        "exposed_data": report.exposed_data,
    }
