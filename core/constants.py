"""
PicoCore V2 Constants

This file contains all centralized constants used in the PicoCore V2.
"""

from micropython import const
import ustruct



# --------------------- Configuration ---------------------

LOGGER_LEVEL = const("system.logger.level")
LOGGER_BUFFER_SIZE = const("system.logger.buffersize")
LOGGER_MAX_FILE_SIZE = const("system.logger.max_file_size")
LOGGER_CONSOLE = const("system.logger.log_to_console")
LOGGER_FILE_LOG = const("system.logger.log_to_file")
LOGGER_MAX_ROTATIONS = const("system.logger.max_rotations")

MESH_ENABLED = const("comms.mesh.enabled")
MESH_SECRET = const("comms.mesh.secret")


# --------------------- Boot ---------------------

BOOT_FLAG = "boot_flag"      # filename stored in flash
BOOT_WINDOW_MS = 1500        # time window to consider a second boot as "double boot"


# --------------------- Logging ---------------------

# Levels as small ints (cheap comparisons)
OFF = const(0)
FATAL = const(1)
ERROR = const(2)
WARN = const(3)
INFO = const(4)
DEBUG = const(5)
TRACE = const(6)

# Map names (optional)
LEVEL_NAMES = {
    FATAL: "FATAL", ERROR: "ERROR", WARN: "WARN",
    INFO: "INFO", DEBUG: "DEBUG", OFF: "OFF", TRACE: "TRACE"
}
LEVEL_NAMES_REV = {
    "FATAL" : FATAL, "ERROR":ERROR, "WARN":WARN,
    "INFO":INFO, "DEBUG":DEBUG,"OFF":OFF,  "TRACE":TRACE
}

LEVEL_BYTES = {
    OFF:   ustruct.pack('B', OFF),
    FATAL: ustruct.pack('B', FATAL),
    ERROR: ustruct.pack('B', ERROR),
    WARN:  ustruct.pack('B', WARN),
    INFO:  ustruct.pack('B', INFO),
    DEBUG: ustruct.pack('B', DEBUG),
    TRACE: ustruct.pack('B', TRACE)
}

# File paths
LOG_FILE_PATH = const("logs.bin")
DATA_FILE_PATH = const("data.txt")

# Data logging csv part

MAX_KEYS = const(32)