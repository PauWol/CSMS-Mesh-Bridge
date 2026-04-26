# CSMS Mesh Bridge Firmware

ESP32 firmware for the **CSMS (Coop Security & Monitoring System) Mesh Bridge**—a UART/ESPNow gateway that bridges the WiFi-based system gateway with a distributed mesh network of IoT devices.

## Overview

The Mesh Bridge operates as a dual-interface hub:
- **UART Interface**: Communicates with the WiFi gateway (which handles web app connectivity)
- **ESPNow Mesh**: Routes messages to/from distributed mesh nodes using a custom protocol with ACK, TTL, and security features

## Features

- **Async I/O**: Built entirely with `uasyncio` for responsive, non-blocking communication
- **Mesh Networking**: Multi-hop ESPNow mesh with automatic neighbor discovery and packet routing
- **UART Protocol**: Structured command/response protocol for gateway integration
- **Logging**: Configurable CSV logging with file rotation and console output
- **Configuration**: TOML-based settings for logger, mesh, and comms parameters

## Technical Stack

- **Platform**: ESP32 running MicroPython 1.26
- **IDE**: PyCharm with MicroPython plugin for development and debugging
- **Communication**: ESPNow mesh + UART serial
- **Architecture**: Modular, async-first design separated by concerns (logging, comms, I/O)

## Project Structure

```
core/
  ├── comms/          # Mesh & communication protocols
  │   ├── mesh/       # ESPNow mesh implementation with routing
  │   └── crc8.py     # Packet integrity checking
  ├── io/             # Hardware interfaces (UART, LED, ADC)
  ├── logging/        # Structured logging with CSV export
  ├── config.py       # Configuration loader
  └── queue.py        # Ring buffer for async message queuing
lib/
  └── uart.py         # UART responder for gateway communication
```

## Quick Start

1. **Install MicroPython 1.26 stubs** on your ESP32
2. **Configure** `config.toml` with mesh/logging settings
3. **Deploy**: Upload all files to the device
4. **Run**: `main.py` starts the bridge (UART + mesh tasks run concurrently)

## Configuration

Edit `config.toml` to customize:
- **Logger**: Level, buffer size, file rotation, console/file output
- **Mesh**: Enable/disable, optional shared secret for encryption

## Protocol

### UART Commands (gateway → bridge)
- `CMD_UART_ACK` - Uart connection check ("ping for gateway")
- `CMD_PING` – Health check ("ping for security-node")
- `CMD_STATUS` – Device status
- `CMD_SENSORS` – Sensor readings
- `CMD_LOG_*` – Logging operations

### Mesh Packets
- Auto-discovery hello/ACK exchange
- Unicast & broadcast with TTL routing
- Optional encryption via shared secret

---

**Version**: 0.0.1 | **Part of**: CSMS Gateway Project

## License

Licensed under AGPL-3.0-or-later © 2026 PauWol
