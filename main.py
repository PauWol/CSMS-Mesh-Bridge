from uasyncio import run, gather

from core.logging import logger
from core.comms.mesh import mesh, mesh_callback

from lib.uart import ESPUartResponder
from lib.data import data

@mesh_callback()
async def _callback(host,msg):
    print(host,msg)
    data().receive(msg)


mesh().start()

async def main():

    uart_res = ESPUartResponder()

    tasks = gather(
        mesh().run(),
        uart_res.run()
    )
    logger().debug("tasks gathered")
    await tasks


if __name__ == '__main__':
    run(main())