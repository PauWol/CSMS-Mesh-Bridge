import struct
from micropython import const

from core.comms.mesh import mesh

def pack(entries: list[tuple[str, int, str]]) -> bytearray:
    """Encode list of (sensor, timestamp, value) → bytearray."""
    buf = bytearray()
    buf.append(len(entries))  # entry count (1 B)

    for sensor, ts, value in entries:
        s = sensor.encode()
        v = value.encode()
        buf.append(len(s))  # sensor str length (1 B)
        buf.extend(s)  # sensor bytes
        buf.extend(struct.pack(">I", ts))  # timestamp uint32 (4 B)
        buf.append(len(v))  # value str length (1 B)
        buf.extend(v)  # value bytes

    return buf


def unpack(buf: bytearray) -> list[tuple[str, int, str]]:
    """Decode bytearray → list of (sensor, timestamp, value)."""
    offset = 0
    n = buf[offset]
    offset += 1
    entries = []

    for _ in range(n):
        s_len = buf[offset]
        offset += 1
        sensor = buf[offset : offset + s_len].decode()
        offset += s_len
        ts = struct.unpack_from(">I", buf, offset)[0]
        offset += 4
        v_len = buf[offset]
        offset += 1
        value = buf[offset : offset + v_len].decode()
        offset += v_len
        entries.append((sensor, ts, value))

    return entries


PIR_IDX = const(0)
PIR_INDICATOR = const("P")

PHC_IDX = const(1)
PHC_INDICATOR = const("C")

RADAR_IDX = const(2)
RADAR_INDICATOR = const("R")


class SensorData:
    def __init__(self):
        self._data = [] * 3

    def pir(self) -> tuple[str,int,str]:
        return self._data[PIR_IDX]

    def photo_cell(self) -> tuple[str,int,str]:
        return self._data[PHC_IDX]

    def radar(self) -> tuple[str,int,str]:
        return self._data[RADAR_IDX]

    def receive(self,payload:bytearray):
        _p = unpack(payload)

        for i in _p:

            if i[0] == PIR_INDICATOR:
                self._data[PIR_IDX] = i
                continue

            if i[0] == PHC_INDICATOR:
                self._data[PHC_IDX] = i
                continue

            if i[0] == RADAR_INDICATOR:
                self._data[RADAR_IDX] = i




_sensor_data = SensorData()


def data():
    global _sensor_data
    return _sensor_data
