import struct

from lib.uart import get_uart

# ── Protocol flags (must match sender) ───────────────────────────────────────
FLAG_PIR    = 0x01
FLAG_PHC    = 0x02
FLAG_RADAR  = 0x04
FLAG_THREAT = 0x08
FLAG_SLEEP  = 0x10
FLAG_VOLT   = 0x20
FLAG_TTE    = 0x40

PKT_VERSION = 1
# constants at top (same as sender)
_PHASE_DEC = {0: "DAY", 1: "DUSK", 2: "NIGHT"}



def unpack(buf):
    """Gateway-side unpack. Returns a dict of present fields."""
    version, flags, base_ts = struct.unpack_from(">BBL", buf, 0)
    offset = 6
    out = {"version": version, "flags": flags, "base_ts": base_ts}

    if flags & FLAG_PIR:
        val, delta = struct.unpack_from(">BH", buf, offset)
        out["pir"] = {"value": bool(val), "ts": base_ts + delta}
        offset += 3

    if flags & FLAG_PHC:
        raw, delta = struct.unpack_from(">HH", buf, offset)
        out["phc"] = {"value": raw / 65535, "ts": base_ts + delta}
        offset += 4

    if flags & FLAG_RADAR:
        dist, energy, delta = struct.unpack_from(">HHH", buf, offset)
        out["radar"] = {"distance": dist, "energy": energy, "ts": base_ts + delta}
        offset += 6

    if flags & FLAG_THREAT:
        score, threshold, phase = struct.unpack_from(">ffB", buf, offset)
        out["threat"] = {
            "score": score,
            "threshold": threshold,
            "phase": _PHASE_DEC.get(phase, "UNKNOWN"),
        }
        offset += 9

    if flags & FLAG_SLEEP:
        (ms,) = struct.unpack_from(">L", buf, offset)
        out["sleep_ms"] = ms
        offset += 4

    if flags & FLAG_VOLT:
        raw, delta = struct.unpack_from(">HH", buf, offset)
        out["volt"] = {"value": raw / 1000, "ts": base_ts + delta}
        offset += 4

    if flags & FLAG_TTE:
        (s,) = struct.unpack_from(">L", buf, offset)
        out["tte_s"] = s

    return out




# ── SensorData ────────────────────────────────────────────────────────────────


class SensorData:
    """
    Holds the most-recently received reading for each sensor channel.
    All fields are None until the first packet containing that channel arrives.
    """

    __slots__ = ("_pir", "_phc", "_radar", "_threat", "_sleep_ms", "_volt", "_tte_s")

    def __init__(self):
        self._pir      = None  # {"value": bool,  "ts": int}
        self._phc      = None  # {"value": float, "ts": int}
        self._radar    = None  # {"distance": int, "energy": int, "ts": int}
        self._threat   = None  # float
        self._sleep_ms = None  # int
        self._volt     = None  # {"value": float, "ts": int}
        self._tte_s    = None  # int

    # ── accessors ─────────────────────────────────────────────────────────────

    def pir(self):
        return self._pir

    def photo_cell(self):
        return self._phc

    def radar(self):
        return self._radar

    def threat(self):
        return self._threat

    def sleep_ms(self):
        return self._sleep_ms

    def volt(self):
        return self._volt

    def tte_s(self):
        return self._tte_s

    def receive(self,payload: bytearray):

        get_uart().send_data(payload)

        parsed = unpack(payload)
        print("RX flags=0x%02x base_ts=%d" % (parsed["flags"], parsed["base_ts"]))

        if "pir" in parsed:
            self._pir = parsed["pir"]  # noqa: E701
        if "phc" in parsed:
            self._phc = parsed["phc"]
        if "radar" in parsed:
            self._radar = parsed["radar"]
        if "threat" in parsed:
            self._threat = parsed["threat"]
        if "sleep_ms" in parsed:
            self._sleep_ms = parsed["sleep_ms"]
        if "volt" in parsed:
            self._volt = parsed["volt"]
        if "tte_s" in parsed:
            self._tte_s = parsed["tte_s"]

        print(self._summary())

    # ── ingress ───────────────────────────────────────────────────────────────

    def _summary(self) -> str:
        parts = []
        if self._pir      is not None: parts.append("pir=%s"      % self._pir["value"])
        if self._phc      is not None: parts.append("phc=%.3f"    % self._phc["value"])
        if self._radar    is not None: parts.append("radar=%dcm"  % self._radar["distance"])
        if self._threat is not None:
            parts.append(
                "threat=%.2f/ %s / %s" % (self._threat["score"], self._threat["phase"],self._threat["threshold"])
            )
        if self._sleep_ms is not None: parts.append("sleep=%dms"  % self._sleep_ms)
        if self._volt     is not None: parts.append("volt=%.3fV"  % self._volt["value"])
        if self._tte_s    is not None: parts.append("tte=%ds"     % self._tte_s)
        return " ".join(parts) if parts else "(empty)"


# ── singleton ─────────────────────────────────────────────────────────────────

_sensor_data: SensorData | None = None


def data() -> SensorData:
    global _sensor_data
    if _sensor_data:
        return _sensor_data
    _sensor_data = SensorData()
    return _sensor_data