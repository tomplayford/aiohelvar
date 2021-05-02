import asyncio
from aiohelvar.router import Router


async def main():

    router = Router("10.254.0.1", 50000)

    await router.initialize()

    await asyncio.sleep(20)

    print(router.devices.devices.items())

asyncio.run(main())
