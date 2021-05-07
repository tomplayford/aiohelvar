
from aiohelvar.exceptions import ParserError, UnrecognizedCommand
from .parser.address import HelvarAddress
from .parser.command_parameter import CommandParameter, CommandParameterType
from .parser.command_type import CommandType
from .parser.command import Command

from copy import copy
import asyncio

PROTOCOL = {
    1: "DALI",
    2: "DIGIDIM",
    3: "SDIM",
    4: "DMX",
}

DALI_TYPES = {
    1: "Fluorescent Lamps",
    2: "Self contained emergency lighting",
    3: "Discharge lamps",
    4: "Low voltage halogen lamps",
    5: "Conversion to D.C.",
    6: "LED modules",
    7: "Switching function",
    8: "Colour control",
    9: "Sequencer",
}

class Device:
    """
    Represents a Helvar device. These map to sensors, lamps and other objects

    The device object is purely represents the device, all acctions on devices
    are preformed with the Devices factory class and various helper functions.
    """
    def __init__(self, address: HelvarAddress, raw_type=None, name=None):
        self.address = address
        self.name = name
        self.state = None
        self.load_level = None
        self.protocol = None
        self.type = None
        self.levels = []
        if raw_type:
            self.decode_raw_type_bytecode(raw_type)

    def __str__(self):
        return f"Device {self.address}: {self.name}. Protocol: {self.protocol}. Type: {self.type}. State: {self.state}. Load: {self.load_level}. Levels: {self.levels}."

    def set_scene_levels(self, levels: list):
        self.levels = levels

    def decode_raw_type_bytecode(self, raw_type):
        """
        """

        raw_type = int(raw_type)

        if raw_type > (2**32) or raw_type < 0:
            raise TypeError

        bytes = [raw_type >> shift & 0xff for shift in [0, 8, 16, 24]]

        try:
            self.protocol = PROTOCOL[bytes[0]]
        except KeyError:
            raise UnrecognizedCommand(None, f"Known device type {bytes} for address {self.address}.")

        if self.protocol == "DALI":
            self.type = DALI_TYPES.get(bytes[1], "Undefined")

        # TODO: Decode other device types.


class Devices:
    def __init__(self, router):
        self.router = router
        self.devices = {}

    def register_device(self, device: Device):
        self.devices[device.address] = device

    def update_device_state(self, address, state):
        self._update_device_param(address, 'state', state)

    def update_device_load_level(self, address, load_level):
        self._update_device_param(address, 'load_level', load_level)

    def update_device_name(self, address, name):
        self._update_device_param(address, 'name', name)

    def _update_device_param(self, address, param, value):
        print(f"Updating {param} on device {address} to {value}")
        try:
            setattr(self.devices[address], param, value)
        except KeyError:
            print(f"Couldn't find device with address: {address}")
            raise

    def update_device_scene_level(self, address, scene_levels):

        levels = scene_levels.split(',')
        if len(levels) != 136:
            raise ParserError(None, f"Expecting 136 scene levels, got {len(levels)}.")

        self.devices[address].set_scene_levels(levels)


    async def set_device_load_level(self, address, load_level, fade_time=1000):
        print(f"Updating device {address} load level to {load_level} over {fade_time}ms...")

        async def task(devices, address, load_level):
            response = await devices.router._send_command_task(
                Command(CommandType.DIRECT_LEVEL_DEVICE,
                        [
                            CommandParameter(CommandParameterType.LEVEL, load_level),
                            CommandParameter(CommandParameterType.FADE_TIME, fade_time)
                        ],
                        command_address=address
                        ))
            print(f"Updated device {address} load level to {load_level}.")
            devices.update_device_load_level(address, response.result)

        asyncio.create_task(task(self, address, load_level))

    async def update_device(self, address):
        # Update name, state and load.

        device = self.devices[address]

        async def update_name(device):
            response = await self.router._send_command_task(
                Command(
                    CommandType.QUERY_DEVICE_DESCRIPTION,
                    command_address=device.address
                )
            )
            self.update_device_name(device.address, response.result)

        async def update_state(device):
            response = await self.router._send_command_task(
                Command(
                    CommandType.QUERY_DEVICE_STATE,
                    command_address=device.address
                )
            )
            self.update_device_state(device.address, response.result)

        async def update_load_level(device):
            response = await self.router._send_command_task(
                Command(
                    CommandType.QUERY_DEVICE_LOAD_LEVEL,
                    command_address=device.address
                )
            )
            self.update_device_load_level(device.address, response.result)

        async def update_scene_level(device):
            response = await self.router._send_command_task(
                Command(
                    CommandType.QUERY_SCENE_INFO,
                    command_address=device.address
                )
            )
            self.update_device_scene_level(device.address, response.result)

        asyncio.create_task(update_name(device))
        asyncio.create_task(update_state(device))
        asyncio.create_task(update_load_level(device))
        asyncio.create_task(update_scene_level(device))


async def receive_and_register_devices(router, command):
    
    command = await router._send_command_task(command)
    
    device_results = command.result.split(",")
    for device_result in device_results:
        device_type, device_address = device_result.split('@')

        address = copy(command.command_address)
        address.device = device_address

        router.devices.register_device(Device(address, device_type))
        await router.devices.update_device(address)


async def get_devices(router):

    [asyncio.create_task(
        receive_and_register_devices(
            router,
            Command(
                CommandType.QUERY_DEVICE_TYPES_AND_ADDRESSES,
                command_address=HelvarAddress(router.cluster_id, router.router_id, subnet_id)))) for subnet_id in range(1, 5)]
