import asyncio

from core.comms.mesh import mesh, mesh_callback
from core import start,task

from lib.uart import ESPUartResponder
from lib.data import data

@task(0,boot=True,parallel=True)
async def init():
    mesh().rx_enable()
    print(mesh().stats())

    uart_res = ESPUartResponder()
    await uart_res.run()


@mesh_callback
async def cbl(host, msg):
    print(f"{host}: {msg}")
    data().receive(msg)
    await asyncio.sleep(0)


start()