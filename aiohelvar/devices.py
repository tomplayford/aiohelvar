
from aiohelvar.exceptions import ParserError, UnrecognizedCommand
from .parser.address import HelvarAddress
from .parser.command_parameter import CommandParameter, CommandParameterType
from .parser.command_type import CommandType
from .parser.command import Command

from copy import copy
import asyncio

import logging

_LOGGER = logging.getLogger(__name__)


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

UNKNOWN_DALI_TYPE = "Unknown DALI Device"
class DigidimType:
    def __init__(self, part_number, name, is_load) -> None:
        self.part_number = part_number
        self.name = name
        self.is_load = is_load
    
    def __str__(self):
        return f"{self.part_number} - {self.name}"

def s(a ,b, c):
    return (a << 16) + (b << 8) + c

UNKNOWN_DIGIDIM_TYPE = DigidimType("0", "Unknown DIGIDIM Device", False)

DIGIDIM_TYPES = {
    s(0x00, 0x10, 0x08): DigidimType("100", "Rotary", False),
    s(0x00, 0x11, 0x07): DigidimType("110", "Single Slider", False),
    s(0x00, 0x11, 0x14): DigidimType("111", "Double Slider", False),
    s(0x00, 0x12, 0x13): DigidimType("121", "2 Button on/off + IR", False),
    s(0x00, 0x12, 0x20): DigidimType("122", "2 Button modifier + IR", False),
    s(0x00, 0x12, 0x44): DigidimType("124", "5 Button + IR", False),
    s(0x00, 0x12, 0x51): DigidimType("125", "5 Button + modifier + IR", False),
    s(0x00, 0x12, 0x68): DigidimType("126", "8 Button + IR", False),
    s(0x00, 0x17, 0x01): DigidimType("170", "IR Receiver", False),
    s(0x00, 0x31, 0x25): DigidimType("312", "Multisensor", False),

    s(0x00, 0x41, 0x08): DigidimType("410", "Ballast Style 1-10V Converter", True),
    s(0x00, 0x41, 0x60): DigidimType("416S", "16A Dimmer", True),
    s(0x00, 0x42, 0x52): DigidimType("425S", "25A Dimmer", True),

    s(0x00, 0x44, 0x43): DigidimType("444", "Multi Input Unit", False),

    s(0x00, 0x45, 0x04): DigidimType("450", "800W Dimmer", True),
    s(0x00, 0x45, 0x28): DigidimType("452", "1000W Universal Dimmer", True),
    s(0x00, 0x45, 0x59): DigidimType("455", "500W Thyristor Dimmer", True),
    s(0x00, 0x45, 0x80): DigidimType("458/DIM8", "8 Channel Dimmer", True),
    s(0x74, 0x45, 0x81): DigidimType("458/CTR8", "8 Channel Ballast Controller", True),
    s(0x04, 0x45, 0x83): DigidimType("458/SW8", "8 Channel Relay Unit", True),
    s(0x00, 0x45, 0x86): DigidimType("458/OPT", "4 Channel Options Module", True),

    s(0x00, 0x46, 0x03): DigidimType("460", "DALI to SDIM Converter", True),
    s(0x00, 0x47, 0x26): DigidimType("472", "Din Rail 1-10V Converter", True),
    s(0x00, 0x47, 0x40): DigidimType("474", "4 Channel Ballast Controller - Output Unit", True),
    s(0x00, 0x47, 0x41): DigidimType("474", "4 Channel Ballast Controller - Relay Unit", True),
    s(0x00, 0x49, 0x00): DigidimType("490", "Blinds Unit", True),
    s(0x00, 0x49, 0x48): DigidimType("494", "Blinds Relay", True),
    s(0x00, 0x49, 0x86): DigidimType("498", "Relay Unit", True),

    s(0x00, 0x80, 0x45): DigidimType("804", "Digidim 4", False),
    s(0x00, 0x92, 0x40): DigidimType("924", "LCD TouchPanel", False),
    s(0x00, 0x93, 0x56): DigidimType("935", "Scene Commander (6 Buttons)", False),
    s(0x00, 0x93, 0x94): DigidimType("939", "Scene Commander (10 Buttons)", False),
    s(0x00, 0x94, 0x24): DigidimType("942", "Analogue Input Unit", False),

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
            try:
                self.type = DALI_TYPES.get(bytes[1], "Undefined")
            except KeyError:
                _LOGGER.error(f"Encountered unknown DALI device type of {raw_type}")
                self.type = UNKNOWN_DALI_TYPE
        if self.protocol == "DIGIDIM":
            try:
                self.type = DIGIDIM_TYPES.get(s(*bytes[:-4:-1]))
            except KeyError:
                _LOGGER.error(f"Encountered unknown DIGIDIM device type of {raw_type}")
                self.type = UNKNOWN_DIGIDIM_TYPE
        
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
        _LOGGER.debug(f"Updating {param} on device {address} to {value}")
        try:
            setattr(self.devices[address], param, value)
        except KeyError:
            _LOGGER.warn(f"Couldn't find device with address: {address}")
            raise

    def update_device_scene_level(self, address, scene_levels):

        levels = scene_levels.split(',')
        if len(levels) != 136:
            raise ParserError(None, f"Expecting 136 scene levels, got {len(levels)}.")

        self.devices[address].set_scene_levels(levels)


    async def set_device_load_level(self, address, load_level, fade_time=1000):
        _LOGGER.info(f"Updating device {address} load level to {load_level} over {fade_time}ms...")

        async def task(devices, address, load_level):
            response = await devices.router._send_command_task(
                Command(CommandType.DIRECT_LEVEL_DEVICE,
                        [
                            CommandParameter(CommandParameterType.LEVEL, load_level),
                            CommandParameter(CommandParameterType.FADE_TIME, fade_time)
                        ],
                        command_address=address
                        ))
            _LOGGER.debug(f"Updated device {address} load level to {load_level}.")
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
