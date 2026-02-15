"""
Known BLE GATT UUIDs — Services, Characteristics, and Descriptors.
Maps standard 16-bit and 128-bit UUIDs to human-readable names.

Usage:
    from gatt_uuids import resolve_uuid, resolve_service, resolve_characteristic

    name = resolve_uuid("00002a19-0000-1000-8000-00805f9b34fb")
    # => "Battery Level"
"""


# ──────────────────────────────────────────────────────────────────────
#  Standard GATT Services  (from bluetooth.com assigned numbers)
# ──────────────────────────────────────────────────────────────────────
SERVICES = {
    "1800": "Generic Access",
    "1801": "Generic Attribute",
    "1802": "Immediate Alert",
    "1803": "Link Loss",
    "1804": "Tx Power",
    "1805": "Current Time",
    "1806": "Reference Time Update",
    "1807": "Next DST Change",
    "1808": "Glucose",
    "1809": "Health Thermometer",
    "180a": "Device Information",
    "180d": "Heart Rate",
    "180e": "Phone Alert Status",
    "180f": "Battery",
    "1810": "Blood Pressure",
    "1811": "Alert Notification",
    "1812": "Human Interface Device",
    "1813": "Scan Parameters",
    "1814": "Running Speed and Cadence",
    "1815": "Automation IO",
    "1816": "Cycling Speed and Cadence",
    "1818": "Cycling Power",
    "1819": "Location and Navigation",
    "181a": "Environmental Sensing",
    "181b": "Body Composition",
    "181c": "User Data",
    "181d": "Weight Scale",
    "181e": "Bond Management",
    "181f": "Continuous Glucose Monitoring",
    "1820": "Internet Protocol Support",
    "1821": "Indoor Positioning",
    "1822": "Pulse Oximeter",
    "1823": "HTTP Proxy",
    "1824": "Transport Discovery",
    "1825": "Object Transfer",
    "1826": "Fitness Machine",
    "1827": "Mesh Provisioning",
    "1828": "Mesh Proxy",
    "1829": "Reconnection Configuration",
    "183a": "Insulin Delivery",
    "183b": "Binary Sensor",
    "183c": "Emergency Configuration",
    "183e": "Physical Activity Monitor",
    "1843": "Audio Input Control",
    "1844": "Volume Control",
    "1845": "Volume Offset Control",
    "1846": "Coordinated Set Identification",
    "1847": "Device Time",
    "1848": "Media Control",
    "1849": "Generic Media Control",
    "184a": "Constant Tone Extension",
    "184b": "Telephone Bearer",
    "184c": "Generic Telephone Bearer",
    "184d": "Microphone Control",
    "184e": "Audio Stream Control",
    "184f": "Broadcast Audio Scan",
    "1850": "Published Audio Capabilities",
    "1851": "Basic Audio Announcement",
    "1852": "Broadcast Audio Announcement",
    "1853": "Common Audio",
    "1854": "Hearing Access",
    "1855": "TMAS",
    "1856": "Public Broadcast Announcement",
}

# ──────────────────────────────────────────────────────────────────────
#  Standard GATT Characteristics
# ──────────────────────────────────────────────────────────────────────
CHARACTERISTICS = {
    "2a00": "Device Name",
    "2a01": "Appearance",
    "2a02": "Peripheral Privacy Flag",
    "2a03": "Reconnection Address",
    "2a04": "Peripheral Preferred Connection Parameters",
    "2a05": "Service Changed",
    "2a06": "Alert Level",
    "2a07": "Tx Power Level",
    "2a08": "Date Time",
    "2a09": "Day of Week",
    "2a0a": "Day Date Time",
    "2a0c": "Exact Time 256",
    "2a0d": "DST Offset",
    "2a0e": "Time Zone",
    "2a0f": "Local Time Information",
    "2a11": "Time with DST",
    "2a12": "Time Accuracy",
    "2a13": "Time Source",
    "2a14": "Reference Time Information",
    "2a16": "Time Update Control Point",
    "2a17": "Time Update State",
    "2a18": "Glucose Measurement",
    "2a19": "Battery Level",
    "2a1c": "Temperature Measurement",
    "2a1d": "Temperature Type",
    "2a1e": "Intermediate Temperature",
    "2a21": "Measurement Interval",
    "2a22": "Boot Keyboard Input Report",
    "2a23": "System ID",
    "2a24": "Model Number String",
    "2a25": "Serial Number String",
    "2a26": "Firmware Revision String",
    "2a27": "Hardware Revision String",
    "2a28": "Software Revision String",
    "2a29": "Manufacturer Name String",
    "2a2a": "IEEE Regulatory Cert Data List",
    "2a2b": "Current Time",
    "2a2c": "Magnetic Declination",
    "2a31": "Scan Refresh",
    "2a32": "Boot Keyboard Output Report",
    "2a33": "Boot Mouse Input Report",
    "2a34": "Glucose Measurement Context",
    "2a35": "Blood Pressure Measurement",
    "2a36": "Intermediate Cuff Pressure",
    "2a37": "Heart Rate Measurement",
    "2a38": "Body Sensor Location",
    "2a39": "Heart Rate Control Point",
    "2a3f": "Alert Status",
    "2a40": "Ringer Control Point",
    "2a41": "Ringer Setting",
    "2a42": "Alert Category ID Bit Mask",
    "2a43": "Alert Category ID",
    "2a44": "Alert Notification Control Point",
    "2a45": "Unread Alert Status",
    "2a46": "New Alert",
    "2a47": "Supported New Alert Category",
    "2a48": "Supported Unread Alert Category",
    "2a49": "Blood Pressure Feature",
    "2a4a": "HID Information",
    "2a4b": "Report Map",
    "2a4c": "HID Control Point",
    "2a4d": "Report",
    "2a4e": "Protocol Mode",
    "2a4f": "Scan Interval Window",
    "2a50": "PnP ID",
    "2a51": "Glucose Feature",
    "2a52": "Record Access Control Point",
    "2a53": "RSC Measurement",
    "2a54": "RSC Feature",
    "2a55": "SC Control Point",
    "2a56": "Digital",
    "2a58": "Analog",
    "2a5a": "Aggregate",
    "2a5b": "CSC Measurement",
    "2a5c": "CSC Feature",
    "2a5d": "Sensor Location",
    "2a63": "Cycling Power Measurement",
    "2a64": "Cycling Power Vector",
    "2a65": "Cycling Power Feature",
    "2a66": "Cycling Power Control Point",
    "2a67": "Location and Speed",
    "2a68": "Navigation",
    "2a69": "Position Quality",
    "2a6a": "LN Feature",
    "2a6b": "LN Control Point",
    "2a6c": "Elevation",
    "2a6d": "Pressure",
    "2a6e": "Temperature",
    "2a6f": "Humidity",
    "2a70": "True Wind Speed",
    "2a71": "True Wind Direction",
    "2a72": "Apparent Wind Speed",
    "2a73": "Apparent Wind Direction",
    "2a74": "Gust Factor",
    "2a75": "Pollen Concentration",
    "2a76": "UV Index",
    "2a77": "Irradiance",
    "2a78": "Rainfall",
    "2a79": "Wind Chill",
    "2a7a": "Heat Index",
    "2a7b": "Dew Point",
    "2a7d": "Descriptor Value Changed",
    "2a7e": "Aerobic Heart Rate Lower Limit",
    "2a7f": "Aerobic Threshold",
    "2a80": "Age",
    "2a81": "Anaerobic Heart Rate Lower Limit",
    "2a82": "Anaerobic Heart Rate Upper Limit",
    "2a83": "Anaerobic Threshold",
    "2a84": "Aerobic Heart Rate Upper Limit",
    "2a85": "Date of Birth",
    "2a86": "Date of Threshold Assessment",
    "2a87": "Email Address",
    "2a88": "Fat Burn Heart Rate Lower Limit",
    "2a89": "Fat Burn Heart Rate Upper Limit",
    "2a8a": "First Name",
    "2a8b": "Five Zone Heart Rate Limits",
    "2a8c": "Gender",
    "2a8d": "Heart Rate Max",
    "2a8e": "Height",
    "2a8f": "Hip Circumference",
    "2a90": "Last Name",
    "2a91": "Maximum Recommended Heart Rate",
    "2a92": "Resting Heart Rate",
    "2a93": "Sport Type for Aerobic and Anaerobic Thresholds",
    "2a94": "Three Zone Heart Rate Limits",
    "2a95": "Two Zone Heart Rate Limits",
    "2a96": "VO2 Max",
    "2a97": "Waist Circumference",
    "2a98": "Weight",
    "2a99": "Database Change Increment",
    "2a9a": "User Index",
    "2a9b": "Body Composition Feature",
    "2a9c": "Body Composition Measurement",
    "2a9d": "Weight Measurement",
    "2a9e": "Weight Scale Feature",
    "2a9f": "User Control Point",
    "2aa0": "Magnetic Flux Density 2D",
    "2aa1": "Magnetic Flux Density 3D",
    "2aa2": "Language",
    "2aa4": "Bond Management Control Point",
    "2aa5": "Bond Management Feature",
    "2aa6": "Central Address Resolution",
    "2aa7": "CGM Measurement",
    "2aa8": "CGM Feature",
    "2aa9": "CGM Status",
    "2aaa": "CGM Session Start Time",
    "2aab": "CGM Session Run Time",
    "2aac": "CGM Specific Ops Control Point",
    "2aad": "Indoor Positioning Configuration",
    "2aae": "Latitude",
    "2aaf": "Longitude",
    "2ab0": "Local North Coordinate",
    "2ab1": "Local East Coordinate",
    "2ab2": "Floor Number",
    "2ab3": "Altitude",
    "2ab4": "Uncertainty",
    "2ab5": "Location Name",
    "2ab6": "URI",
    "2ab7": "HTTP Headers",
    "2ab8": "HTTP Status Code",
    "2ab9": "HTTP Entity Body",
    "2aba": "HTTP Control Point",
    "2abb": "HTTPS Security",
    "2abc": "TDS Control Point",
    "2abd": "OTS Feature",
    "2abe": "Object Name",
    "2abf": "Object Type",
    "2ac0": "Object Size",
    "2ac1": "Object First-Created",
    "2ac2": "Object Last-Modified",
    "2ac3": "Object ID",
    "2ac4": "Object Properties",
    "2ac5": "Object Action Control Point",
    "2ac6": "Object List Control Point",
    "2ac7": "Object List Filter",
    "2ac8": "Object Changed",
    "2ac9": "Resolvable Private Address Only",
    "2acc": "Fitness Machine Feature",
    "2acd": "Treadmill Data",
    "2ace": "Cross Trainer Data",
    "2acf": "Step Climber Data",
    "2ad0": "Stair Climber Data",
    "2ad1": "Rower Data",
    "2ad2": "Indoor Bike Data",
    "2ad3": "Training Status",
    "2ad4": "Supported Speed Range",
    "2ad5": "Supported Inclination Range",
    "2ad6": "Supported Resistance Level Range",
    "2ad7": "Supported Heart Rate Range",
    "2ad8": "Supported Power Range",
    "2ad9": "Fitness Machine Control Point",
    "2ada": "Fitness Machine Status",
    "2aed": "Date UTC",
    "2b29": "Client Supported Features",
    "2b2a": "Database Hash",
    "2b3a": "Server Supported Features",
}

# ──────────────────────────────────────────────────────────────────────
#  Standard GATT Descriptors
# ──────────────────────────────────────────────────────────────────────
DESCRIPTORS = {
    "2900": "Characteristic Extended Properties",
    "2901": "Characteristic User Description",
    "2902": "Client Characteristic Configuration (CCCD)",
    "2903": "Server Characteristic Configuration",
    "2904": "Characteristic Presentation Format",
    "2905": "Characteristic Aggregate Format",
    "2906": "Valid Range",
    "2907": "External Report Reference",
    "2908": "Report Reference",
    "2909": "Number of Digitals",
    "290a": "Value Trigger Setting",
    "290b": "Environmental Sensing Configuration",
    "290c": "Environmental Sensing Measurement",
    "290d": "Environmental Sensing Trigger Setting",
    "290e": "Time Trigger Setting",
}

# ──────────────────────────────────────────────────────────────────────
#  Well-known vendor / custom service UUIDs
# ──────────────────────────────────────────────────────────────────────
VENDOR_SERVICES = {
    # Nordic Semiconductor
    "6e400001-b5a3-f393-e0a9-e50e24dcca9e": "Nordic UART Service (NUS)",
    # Texas Instruments SensorTag
    "f000aa00-0451-4000-b000-000000000000": "TI IR Temperature",
    "f000aa20-0451-4000-b000-000000000000": "TI Humidity",
    "f000aa40-0451-4000-b000-000000000000": "TI Barometer",
    "f000aa80-0451-4000-b000-000000000000": "TI Movement",
    "f000aa70-0451-4000-b000-000000000000": "TI Light",
    # ESP32 default
    "000000ff-0000-1000-8000-00805f9b34fb": "ESP32 Custom Service",
    # Apple
    "7905f431-b5ce-4e99-a40f-4b1e122d00d0": "Apple Notification Center (ANCS)",
    "89d3502b-0f36-433a-8ef4-c502ad55f8dc": "Apple Media Service (AMS)",
    "d0611e78-bbb4-4591-a5f8-487910ae4366": "Apple Current Time",
    # Google / Eddystone
    "0000feaa-0000-1000-8000-00805f9b34fb": "Eddystone",
    # DFU Services
    "00001530-1212-efde-1523-785feabcd123": "Nordic DFU Service",
    "0000fe59-0000-1000-8000-00805f9b34fb": "Nordic Secure DFU",
    # SMP (MCUmgr)
    "8d53dc1d-1db7-4cd3-868b-8a527460aa84": "SMP Service (MCUmgr)",
}

VENDOR_CHARACTERISTICS = {
    # Nordic UART
    "6e400002-b5a3-f393-e0a9-e50e24dcca9e": "NUS RX (Write)",
    "6e400003-b5a3-f393-e0a9-e50e24dcca9e": "NUS TX (Notify)",
    # SMP
    "da2e7828-fbce-4e01-ae9e-261174997c48": "SMP Characteristic",
    # Nordic DFU
    "00001531-1212-efde-1523-785feabcd123": "DFU Control Point",
    "00001532-1212-efde-1523-785feabcd123": "DFU Packet",
    "00001534-1212-efde-1523-785feabcd123": "DFU Version",
}


def _extract_short_uuid(uuid: str) -> str | None:
    """Extract 16-bit UUID from standard 128-bit form (0000XXXX-0000-1000-8000-00805f9b34fb)."""
    uuid = uuid.lower().strip()
    if len(uuid) == 36 and uuid.endswith("-0000-1000-8000-00805f9b34fb"):
        return uuid[4:8]
    if len(uuid) == 4:
        return uuid
    return None


def resolve_service(uuid: str) -> str:
    """Resolve a service UUID to a human-readable name."""
    uuid = uuid.lower().strip()
    
    # Check vendor services (full 128-bit)
    if uuid in VENDOR_SERVICES:
        return VENDOR_SERVICES[uuid]
    
    # Check standard 16-bit
    short = _extract_short_uuid(uuid)
    if short and short in SERVICES:
        return SERVICES[short]
    
    return "Unknown Service"


def resolve_characteristic(uuid: str) -> str:
    """Resolve a characteristic UUID to a human-readable name."""
    uuid = uuid.lower().strip()
    
    # Check vendor characteristics (full 128-bit)
    if uuid in VENDOR_CHARACTERISTICS:
        return VENDOR_CHARACTERISTICS[uuid]
    
    # Check standard 16-bit
    short = _extract_short_uuid(uuid)
    if short and short in CHARACTERISTICS:
        return CHARACTERISTICS[short]
    
    return "Unknown"


def resolve_descriptor(uuid: str) -> str:
    """Resolve a descriptor UUID to a human-readable name."""
    short = _extract_short_uuid(uuid)
    if short and short in DESCRIPTORS:
        return DESCRIPTORS[short]
    return "Unknown Descriptor"


def resolve_uuid(uuid: str) -> str:
    """Try to resolve any UUID (service, characteristic, or descriptor)."""
    uuid = uuid.lower().strip()
    
    # Full 128-bit vendor lookup
    if uuid in VENDOR_SERVICES:
        return VENDOR_SERVICES[uuid]
    if uuid in VENDOR_CHARACTERISTICS:
        return VENDOR_CHARACTERISTICS[uuid]
    
    # Standard 16-bit lookup
    short = _extract_short_uuid(uuid)
    if short:
        if short in SERVICES:
            return SERVICES[short]
        if short in CHARACTERISTICS:
            return CHARACTERISTICS[short]
        if short in DESCRIPTORS:
            return DESCRIPTORS[short]
    
    return "Unknown"


def is_standard_uuid(uuid: str) -> bool:
    """Check if a UUID is a standard Bluetooth SIG UUID."""
    return _extract_short_uuid(uuid) is not None


def format_uuid_with_name(uuid: str, resolve_fn=resolve_uuid) -> str:
    """Format a UUID with its resolved name, e.g. '0x2A19 Battery Level'."""
    name = resolve_fn(uuid)
    short = _extract_short_uuid(uuid)
    if short:
        return f"0x{short.upper()} {name}"
    if name != "Unknown" and name != "Unknown Service":
        return f"{name}"
    return uuid
