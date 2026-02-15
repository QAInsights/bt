import asyncio
from typing import Callable, List
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

class BleManager:
    """Async wrapper around bleak for scanning, connecting, writing and listening."""

    async def scan(self, timeout: float = 5.0) -> List[BLEDevice]:
        devices = await BleakScanner.discover(timeout=timeout)
        return devices

    async def connect(self, address: str, timeout: float = 10.0) -> BleakClient:
        client = BleakClient(address, timeout=timeout)
        await client.connect()
        return client

    async def get_services(self, client: BleakClient) -> dict:
        """Get services and characteristics from connected device."""
        services = client.services
        result = {}
        for service in services:
            result[service.uuid] = {
                "description": service.description or "N/A",
                "characteristics": {}
            }
            for char in service.characteristics:
                props = char.properties
                result[service.uuid]["characteristics"][char.uuid] = {
                    "description": char.description or "N/A",
                    "properties": props
                }
        return result

    async def read_char(self, client: BleakClient, char_uuid: str) -> bytes:
        """Read from a characteristic on an existing connection."""
        return await client.read_gatt_char(char_uuid)

    async def write_char(self, client: BleakClient, char_uuid: str, data: bytes | str):
        """Write to a characteristic on an existing connection."""
        if isinstance(data, str):
            data = data.encode()
        await client.write_gatt_char(char_uuid, data)

    async def listen(self, address: str, char_uuid: str, callback: Callable[[int, bytearray], None]):
        async with BleakClient(address) as client:
            await client.connect()
            await client.start_notify(char_uuid, callback)
            # run until cancelled
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                await client.stop_notify(char_uuid)
                raise
