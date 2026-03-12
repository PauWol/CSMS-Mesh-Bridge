"""
CSMS – ESPNOW & UART Bridge
"""

from uasyncio import run, create_task, gather

from core.logging import logger
from core.comms.mesh import mesh, mesh_callback
from lib.uart import ESPUartResponder

def _callback(host,msg):
    print(host,msg)



async def main():
    mesh_res = mesh(auto_init=True)

    mesh_res.callback(_callback)
    uart_res = ESPUartResponder()

    tasks = gather(
        mesh_res.receive_task(),
        uart_res.run()
    )
    logger().debug("tasks gathered")
    await tasks


if __name__ == '__main__':
    run(main())