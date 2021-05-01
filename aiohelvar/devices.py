
from aiohelvar.parser.address import HelvarAddress
from aiohelvar.parser.command_parameter import CommandParameter, CommandParameterType
from .parser.command_type import CommandType
from .parser.command import Command

from copy import copy

class Device:
    def __init__(self, address: HelvarAddress, type=None, description=None):
        self.address = address
        self.description = None
        self.state = None
        self.load_level = None

    def __str__(self):
        return f"Device {self.address}: {self.description}. State: {self.state}. Load: {self.load_level}."


async def create_devices_from_command(router, commands):

    devices = []

    for command in commands:
        device_results = command.result.split(",")
        for device_result in device_results:
            device_type, device_address = device_result.split('@')

            address = copy(command.command_address)
            address.device = device_address

            devices.append(Device(address, device_type))

    print(f"Found {len(devices)} devices")

    for device in devices:

        response = await router.send_command(
            Command(
                CommandType.QUERY_DEVICE_DESCRIPTION,
                command_address=device.address
            )
        )
        await response
        device.description = response.result().result

        response = await router.send_command(
            Command(
                CommandType.QUERY_DEVICE_STATE,
                command_address=device.address
            )
        )
        await response
        device.state = response.result().result

        response = await router.send_command(
            Command(
                CommandType.QUERY_DEVICE_LOAD_LEVEL,
                command_address=device.address
            )
        )
        await response
        device.load_level = response.result().result

    return devices
