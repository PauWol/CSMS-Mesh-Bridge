import uasyncio as asyncio
from core import get_onboard_led
from machine import UART, Pin
import ujson
import utime

from core.logging import logger
from core.io import NeoLed

from comms_commands import ping

# Protocol constants
COMMAND_PREFIX     = "cmd:"
COMMAND_DELIMITER  = ";"
COMMAND_TERMINATOR = ":end"

CMD_UART_ACK     = "UAK"
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

# The Pi's DEFAULT_TIMEOUT for _request is 5.0 s.
# We must respond within that window, so the mesh ping gets a shorter budget
# to ensure the UART response always arrives before the Pi gives up.
_MESH_PING_TIMEOUT = 3.5  # seconds – leaves 1.5 s margin on a 5 s Pi timeout

STATUS_LED_PIN = get_onboard_led()


def get_log_info() -> dict:
    """
    TODO: replace with real log metadata read.
    """
    return {
        "id":       1,
        "source":   "espnow-mcu",
        "coverage": "0-0",          # TODO: real entry range e.g. "0-142"
    }


def get_log_entries(log_id: int) -> list:
    """
    TODO: replace with actual log retrieval by id.
    """
    return [
        {"id": log_id, "source": "espnow-mcu", "coverage": "0-10"},
        {"id": log_id, "source": "espnow-mcu", "coverage": "10-20"},
    ]


class ESPUartResponder:
    """
    Listens on UART2 (GP16/GP17) for command frames from the WIFI-MCU,
    dispatches each command to the matching handler, and writes the response
    back on the same UART.

    Status LED blinks once for every command that is received.
    """

    def __init__(self):
        import gc
        gc.collect()

        self._uart = UART(
            UART_ID,
            baudrate=BAUD_RATE,
            bits=8,
            parity=None,
            stop=1,
            timeout=100,
            tx=Pin(UART_TX),
            rx=Pin(UART_RX),
            rxbuf=512,
        )

        self.led = NeoLed(STATUS_LED_PIN[1])

    # ── Wire encoding ─────────────────────────────────────────────────────────

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
    def _decode(raw: str) -> tuple:
        """
        Parse a raw frame into (command_token, parameters_dict).
        Raises ValueError for malformed frames.
        """
        raw = raw.strip()
        if not raw.startswith(COMMAND_PREFIX) or not raw.endswith(COMMAND_TERMINATOR):
            raise ValueError("Bad frame: {!r}".format(raw))

        body  = raw[len(COMMAND_PREFIX):-len(COMMAND_TERMINATOR)]
        # Split on first delimiter only – JSON values may contain COMMAND_DELIMITER
        parts = body.split(COMMAND_DELIMITER, 1)

        command = parts[0]
        params  = ujson.loads(parts[1]) if len(parts) == 2 and parts[1] else {}
        return command, params

    # ── Low-level I/O ─────────────────────────────────────────────────────────

    def _write(self, command: str, parameters: dict):
        self._uart.write(self._encode(command, parameters))

    def send_data(self, data: bytearray):
        """Forward a raw binary sensor frame to the Pi."""
        self._uart.write(data)

    async def _read_line(self):
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

    # ── Command handlers ──────────────────────────────────────────────────────

    async def _handle_uart_ack(self, _params: dict):
        """Immediate physical-layer ACK – no external calls, always fast."""
        self._write(CMD_UART_ACK, {"status": "ok"})
        await asyncio.sleep_ms(0)

    async def _handle_ping(self, _params: dict):
        """
        Forward a liveness probe to the security node via mesh and relay the
        result.  Uses _MESH_PING_TIMEOUT (< Pi's UART timeout) so we always
        write the response before the Pi gives up waiting.
        """
        st = "ok"
        if not await ping(timeout=_MESH_PING_TIMEOUT):
            st = "unconnected"
        self._write(CMD_PING, {"status": st})

    async def _handle_log_info(self, _params: dict):
        self._write(CMD_LOG_INFO, get_log_info())
        await asyncio.sleep_ms(0)

    async def _handle_log_download(self, params: dict):
        log_id  = int(params.get("id", 0))
        entries = get_log_entries(log_id)
        for entry in entries:
            self._write(CMD_LOG_DOWNLOAD, entry)
        # Empty terminator frame signals end-of-stream to the host
        self._write(CMD_LOG_DOWNLOAD, {})
        await asyncio.sleep_ms(0)

    _HANDLERS = {
        CMD_PING:         _handle_ping,
        CMD_LOG_INFO:     _handle_log_info,
        CMD_LOG_DOWNLOAD: _handle_log_download,
        CMD_UART_ACK:     _handle_uart_ack,
    }

    async def _dispatch(self, command: str, params: dict):
        handler = self._HANDLERS.get(command)
        if handler:
            await handler(self, params)
        else:
            logger().warn("UART Unknown command: {!r}".format(command))
            self._write(command, {"error": "unknown_command"})
            await asyncio.sleep_ms(0)

    # ── Main loop ─────────────────────────────────────────────────────────────

    async def run(self):
        logger().debug("UART Responder started – listening on GP16/GP17")

        while True:
            line = await self._read_line()

            if not line:
                continue

            asyncio.create_task(self._blink_led())

            try:
                command, params = self._decode(line)
                logger().debug("UART <- {} params={}".format(command, params))
                await self._dispatch(command, params)

            except ValueError as e:
                logger().error("UART Frame error: {}".format(e))


# ── Singleton ─────────────────────────────────────────────────────────────────

_resp = None


def get_uart():
    global _resp
    if _resp:
        return _resp
    _resp = ESPUartResponder()
    return _resp