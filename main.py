import asyncio

from core.comms.mesh import mesh, mesh_callback
from core import start,task

from lib.uart import get_uart
from lib.data import data



@task(0,boot=True,parallel=True)
async def init():
    mesh().rx_enable()
    print(mesh().stats())

    await get_uart().run()


@mesh_callback(raw=True)
async def cbl(host, msg):
    print(f"{host}: {msg}")
    data().receive(msg)
    await asyncio.sleep(0)


start()