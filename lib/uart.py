import uasyncio as asyncio
from core import ONBOARD_LED
from machine import UART, Pin
import ujson
import utime

from core.logging import logger

# Protocol constants
COMMAND_PREFIX     = "cmd:"
COMMAND_DELIMITER  = ";"
COMMAND_TERMINATOR = ":end"

CMD_PING         = "PNG"
CMD_STATUS       = "STS"
CMD_SENSORS      = "SNS"
CMD_LOG_INFO     = "LGI"
CMD_LOG_DOWNLOAD = "LGD"

# Pin config
UART_ID   = 1        # UART2 on ESP32
UART_TX   = 17       # GP17 → peer RX
UART_RX   = 16       # GP16 ← peer TX
BAUD_RATE = 115200

STATUS_LED_PIN = ONBOARD_LED


# ══════════════════════════════════════════════════════════════════════════════
# MOCK STATE  —  replace these with your real data sources
# ══════════════════════════════════════════════════════════════════════════════

def get_status() -> dict:
    """
    TODO: replace with real MCU state.
    Should return current wake/sleep schedule and threat assessment.
    """
    return {
        "nextWake":      utime.time() + 300,   # TODO: read from scheduler
        "sleepInterval": 300,                   # TODO: read from config
        "lastSync":      utime.time() - 60,    # TODO: read from sync manager
        "threatScore":   0,                     # TODO: read from threat engine
    }


def get_sensors() -> dict:
    """
    TODO: replace with real sensor read logic.
    Should return the latest sensor sample.
    """
    return {
        "name":      "mock_sensor",             # TODO: real sensor name
        "value":     "0.00",                    # TODO: real sensor value (as str)
        "timestamp": utime.time(),
    }


def get_log_info() -> dict:
    """
    TODO: replace with real log metadata read.
    """
    return {
        "id":       1,                          # TODO: read from log store
        "source":   "espnow-mcu",              # TODO: real source label
        "coverage": "0-0",                      # TODO: real entry range e.g. "0-142"
    }


def get_log_entries(log_id: int) -> list:
    """
    TODO: replace with actual log retrieval by id.
    Should return a list of dicts, each matching LogInfoResponse shape.
    """
    return [
        {"id": log_id, "source": "espnow-mcu", "coverage": "0-10"},   # TODO: real entries
        {"id": log_id, "source": "espnow-mcu", "coverage": "10-20"},
    ]


class ESPUartResponder:
    """
    Listens on UART2 (GP16/GP17) for command frames from the WIFI-MCU,
    dispatches each command to the matching handler, and writes the response
    back on the same UART.

    Status LED (GP18) blinks once for every command that is received.
    """

    def __init__(self):
        import gc

        gc.collect()
        print("FREE:", gc.mem_free())

        # Deinit first — soft reboot leaves ESP-IDF UART driver installed
        _cleanup = UART(UART_ID, tx=Pin(UART_TX), rx=Pin(UART_RX))
        _cleanup.deinit()

        self._uart = UART(
            UART_ID,
            baudrate=BAUD_RATE,
            bits=8,
            parity=None,
            stop=1,
            timeout=100,
            tx=Pin(UART_TX),
            rx=Pin(UART_RX),
            rxbuf=256,
        )
        self.led = Pin(STATUS_LED_PIN, Pin.OUT)

    @staticmethod
    def _encode(command: str, parameters: dict) -> bytes:
        return (
            COMMAND_PREFIX
            + command
            + COMMAND_DELIMITER
            + ujson.dumps(parameters)
            + COMMAND_TERMINATOR
            + "\n"
        ).encode()

    @staticmethod
    def _decode(raw: str) -> tuple[str, dict]:
        """
        Parse a raw frame into (command_token, parameters_dict).
        Raises ValueError for malformed frames.
        """
        raw = raw.strip()
        if not raw.startswith(COMMAND_PREFIX) or not raw.endswith(COMMAND_TERMINATOR):
            raise ValueError(f"Bad frame: {raw!r}")

        body  = raw[len(COMMAND_PREFIX):-len(COMMAND_TERMINATOR)]
        parts = body.split(COMMAND_DELIMITER, 1)   # max 1 split → safe for JSON values

        command = parts[0]
        params  = ujson.loads(parts[1]) if len(parts) == 2 and parts[1] else {}
        return command, params

    def _write(self, command: str, parameters: dict):
        self._uart.write(self._encode(command, parameters))

    async def _read_line(self) -> str | None:
        """Return the next complete line or None if nothing is available yet."""
        if self._uart.any():
            raw = self._uart.readline()
            if raw:
                return raw.decode().strip()

        await asyncio.sleep_ms(2)
        return None

    async def _blink_led(self):
        self.led.on()
        await asyncio.sleep_ms(30)
        self.led.off()

    def _handle_ping(self, _params: dict):
        self._write(CMD_PING, {"status": "ok"})

    def _handle_status(self, _params: dict):
        self._write(CMD_STATUS, get_status())

    def _handle_sensors(self, _params: dict):
        self._write(CMD_SENSORS, get_sensors())

    def _handle_log_info(self, _params: dict):
        self._write(CMD_LOG_INFO, get_log_info())

    def _handle_log_download(self, params: dict):
        log_id  = int(params.get("id", 0))
        entries = get_log_entries(log_id)
        for entry in entries:
            self._write(CMD_LOG_DOWNLOAD, entry)
        # Empty terminator frame signals end-of-stream to the host
        self._write(CMD_LOG_DOWNLOAD, {})

    _HANDLERS = {
        CMD_PING:         _handle_ping,
        CMD_STATUS:       _handle_status,
        CMD_SENSORS:      _handle_sensors,
        CMD_LOG_INFO:     _handle_log_info,
        CMD_LOG_DOWNLOAD: _handle_log_download,
    }

    def _dispatch(self, command: str, params: dict):
        handler = self._HANDLERS.get(command)
        if handler:
            handler(self, params)
        else:
            logger().warn(f"UART Unknown command: {command!r}")
            self._write(command, {"error": "unknown_command"})

    async def run(self):
        logger().debug("UART Responder started – listening on GP16/GP17")

        while True:
            line = await self._read_line()

            if not line:
                continue

            asyncio.create_task(self._blink_led())

            try:
                command, params = self._decode(line)
                logger().debug(f"UART ← {command} params={params}")
                self._dispatch(command, params)

            except ValueError as e:
                logger().error(f"UART Frame error: {e}")

async def main():
    responder = ESPUartResponder()

    await responder.run()