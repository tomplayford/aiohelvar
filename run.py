import asyncio
from aiohelvar.router import Router
from aiohelvar.parser.address import HelvarAddress

async def main():

    router = Router("10.254.0.1", 50000)

    await router.initialize()

    await asyncio.sleep(10)

    for key, value in router.devices.devices.items():
        print(f"{key}: {value}")

    for key, value in router.groups.groups.items():
        print(f"{key}: {value}")
    
    for key, value in router.scenes.scenes.items():
        print(f"{key}: {value}")
    

    # await router.devices.set_device_load_level(HelvarAddress(0, 1, 2, 60), 95.2, 100)

    # await asyncio.sleep(10)

    # await router.devices.set_device_load_level(HelvarAddress(0, 1, 2, 60), 0.1, 100)

    # await asyncio.sleep(200)

asyncio.run(main())
