"""
MH-Z19 (B / C) CO2 sensor reader for Raspberry Pi Zero 2W (Ver.1)
- Uses /dev/serial0 via pyserial
- Implements request 0xFF 0x01 0x86, parses 9-byte response with checksum
- Retries and port auto-reopen to enhance robustness against contention/errors
"""
from __future__ import annotations
import time
from typing import Optional

class MHZ19Reader:
    def __init__(self, port: str = "/dev/serial0", baudrate: int = 9600, timeout: float = 1.0, retries: int = 3):
        self.port_name = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.retries = retries
        self._ser: Optional[object] = None

    def open(self) -> None:
        if self._ser is not None:
            try:
                # hasattr guard for runtime without pyserial
                if getattr(self._ser, "is_open", False):
                    return
            except Exception:
                pass
        try:
            import serial  # type: ignore
        except Exception as e:
            raise RuntimeError("pyserial is required for MH-Z19. Please install with: pip install pyserial") from e
        self._ser = serial.Serial(self.port_name, self.baudrate, timeout=self.timeout)
        # Sensor warmup might be required; handled by main if needed

    def close(self) -> None:
        try:
            if self._ser:
                self._ser.close()
        except Exception:
            pass
        finally:
            self._ser = None

    @staticmethod
    def _checksum(response: bytes) -> int:
        # Checksum: 0xFF - (sum(bytes[1:8]) % 256) + 1
        return (0xFF - (sum(response[1:8]) & 0xFF) + 1) & 0xFF

    def read_co2(self) -> Optional[int]:
        cmd = bytes([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0x79])
        for attempt in range(self.retries):
            try:
                self.open()
                assert self._ser is not None
                self._ser.reset_input_buffer()
                self._ser.reset_output_buffer()
                self._ser.write(cmd)
                self._ser.flush()
                data = self._ser.read(9)
                if len(data) != 9:
                    time.sleep(0.2)
                    continue
                if data[0] != 0xFF or data[1] != 0x86:
                    time.sleep(0.2)
                    continue
                if self._checksum(data) != data[8]:
                    time.sleep(0.2)
                    continue
                co2 = data[2] * 256 + data[3]
                return co2
            except Exception:
                # Reopen port on failure
                self.close()
                time.sleep(0.5)
                continue
        return None
