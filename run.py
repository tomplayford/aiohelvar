from aiohelvar.parser.address import SceneAddress
import asyncio
from aiohelvar.router import Router
import logging

logging.basicConfig(level=logging.DEBUG)

async def main():

    # console = logging.StreamHandler()
    # console.setLevel(logging.DEBUG)

    # logging.getLogger().addHandler(console)

    

    router = Router("10.254.0.1", 50000)

    await router.connect()

    await asyncio.sleep(5)

    await router.send_string(">V:2,C:14,L:0.0,F:1000,@0.1.1.16#")

    await router.send_string(">V:2,C:14,L:100.0,F:1000,@0.1.1.16#")

    await router.send_string(">V:2,C:107#")

    # for key, value in router.devices.devices.items():
    #     print(f"{key}: {value}")
    #     print(f"Device {key} states are: {value._get_states()}")

    # for key, value in router.groups.groups.items():
    #     print(f"{key}: {value}")

    # for key, value in router.scenes.scenes.items():
    #     print(f"{key}: {value}")

    # await asyncio.sleep(2)

    # print("setting new scene")
    # await router.groups.set_scene(SceneAddress(10,1,2), 50)

    # print("sleeping...")
    # await asyncio.sleep(5)
    # print("setting new scene")
    # await router.groups.set_scene(SceneAddress(10,1,3), 50)

    # await router.devices.set_device_load_level(HelvarAddress(0, 1, 2, 60), 95.2, 100)

    # await asyncio.sleep(10)

    # await router.devices.set_device_load_level(HelvarAddress(0, 1, 2, 60), 0.1, 100)

    await asyncio.sleep(200)

asyncio.run(main())
