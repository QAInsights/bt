import pytest
from typer.testing import CliRunner
import bt as cli

runner = CliRunner()

class DummyDevice:
    def __init__(self, name, address):
        self.name = name
        self.address = address

@pytest.fixture(autouse=True)
def patch_ble(monkeypatch):
    class FakeManager:
        async def scan(self, timeout=5.0):
            return [DummyDevice("DevA", "AA:BB:CC:DD:EE:01"), DummyDevice(None, "AA:BB:CC:DD:EE:02")]
        async def connect(self, address, timeout=10.0):
            class C:
                async def disconnect(self):
                    return True
            return C()
        async def write_char(self, address, char_uuid, data):
            return True
        async def listen(self, address, char_uuid, callback):
            # simulate one callback then return
            callback(1, bytearray(b"hi"))
    monkeypatch.setattr(cli, "manager", FakeManager())

def test_scan_list():
    result = runner.invoke(cli.app, ["scan", "--no-select" ])
    assert "Bluetooth Devices" in result.output
    assert "DevA" in result.output

def test_connect():
    result = runner.invoke(cli.app, ["connect", "AA:BB:CC:DD:EE:01"], input="\n")
    assert "Connected" in result.output

def test_write():
    result = runner.invoke(cli.app, ["write", "AA:BB:CC:DD:EE:01", "1234", "hello"]) 
    assert "Write successful" in result.output

def test_listen():
    result = runner.invoke(cli.app, ["listen", "AA:BB:CC:DD:EE:01", "1234"], catch_exceptions=False)
    assert "Notification" in result.output
