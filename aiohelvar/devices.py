from aiohelvar.lib import Subscribable
from .static import (
    DALI_TYPES,
    DEVICE_STATE_FLAGS,
    DIGIDIM_TYPES,
    DigidimType,
    PROTOCOL,
    UNKNOWN_DALI_TYPE,
    UNKNOWN_DIGIDIM_TYPE,
    UNKNOWN_PROTOCOL,
    h_2_d,
)
from .exceptions import ParserError, UnrecognizedCommand
from .parser.address import HelvarAddress, SceneAddress
from .parser.command_parameter import CommandParameter, CommandParameterType
from .parser.command_type import CommandType
from .parser.command import Command

from copy import copy
import asyncio

import logging

_LOGGER = logging.getLogger(__name__)


def d_2_h(d):
    return [hex(d >> shift & 0xFF) for shift in [0, 8, 16, 24]]


class Device(Subscribable):
    """
    Represents a Helvar device. These map to sensors, drivers, relays etc.
    """

    def __init__(self, address: HelvarAddress, raw_type=None, name=None):
        super(Device, self).__init__()

        self.address = address
        self.name = name
        self.state = 0
        # Helvar stores brightness as a float between 0 and 100.
        self.load_level: float = 0.0
        self.last_load_level: float = 0.0
        self.last_scene = None
        self.protocol = None
        self.type = None
        self.levels = []

        if raw_type:
            self.decode_raw_type_bytecode(raw_type)

    def __str__(self):
        return f"Device {self.address}: {self.name}. Protocol: {self.protocol}. Type: {self.type}. State: {self.state}. Load: {self.load_level}."

    def _get_states(self):
        states = {}

        for mask, state in DEVICE_STATE_FLAGS.items():
            states[state.state] = int(self.state) & mask > 0

        return states

    @property
    def brightness(self):
        """Translate load level to 0-255 brightness value"""
        return int(self.load_level * 2.55)

    @property
    def is_disabled(self):
        return self._get_states["NSDisabled"]

    @property
    def is_missing(self):
        return self._get_states["NSMissing"]

    @property
    def is_faulty(self):
        return self._get_states["NSFaulty"]

    @property
    def is_lamp_failure(self):
        return self._get_states["NSLampFailure"]

    def set_scene_levels(self, levels: list):
        if self.is_load:
            self.levels = levels

    @property
    def is_light(self):
        return self.is_load

    @property
    def is_load(self):
        """Loads can have scene values, and can have load levels set."""
        if self.protocol == "DALI":
            return True
        if self.protocol == "DIGIDIM":
            return self.type.is_load

        else:
            return True

    async def _set_level(self, level: float):
        if not self.is_load:
            return

        if level < 0:
            level = 0.0
        if level > 100:
            level == 100.0

        if level == 0 and self.load_level > 0:
            self.last_load_level = float(self.load_level)

        self.load_level = float(level)

    async def set_scene_level(self, scene_address: SceneAddress):

        if not self.is_load:
            return

        level = self.get_level_for_scene(scene_address)

        self.last_scene = scene_address

        if level == "*" or level is None:
            return

        if level == "L":
            # Last level before device was powered off.
            level = self.last_load_level
        else:
            level = float(level)

        _LOGGER.debug(
            f"Device {self.address} has {len(self.subscriptions)} subscribers, about to update them..."
        )

        await self._set_level(level)

        await self.update_subscribers()

    def get_level_for_scene(self, scene_address: SceneAddress):

        if self.levels is None or not self.is_load:
            return None

        try:
            return self.levels[scene_address.to_device_int()]
        except IndexError:
            _LOGGER.error(
                f"Couldn't find scene {scene_address} ({scene_address.to_device_int()}) in device {self.address}. Device has {len(self.levels)} known scene levels. "
            )
            raise

    def decode_raw_type_bytecode(self, raw_type):

        raw_type = int(raw_type)

        if raw_type > (2 ** 32) or raw_type < 0:
            raise TypeError

        bytes = [raw_type >> shift & 0xFF for shift in [0, 8, 16, 24]]

        try:
            self.protocol = PROTOCOL[bytes[0]]
        except KeyError:
            self.protocol = UNKNOWN_PROTOCOL
            _LOGGER.error(
                UnrecognizedCommand(
                    None, f"Known device type {bytes} for address {self.address}."
                )
            )

        if self.protocol == "DALI":
            try:
                self.type = DALI_TYPES[bytes[1]]
            except KeyError:
                _LOGGER.error(
                    f"Encountered unknown DALI device type of {d_2_h(raw_type)}"
                )
                self.type = UNKNOWN_DALI_TYPE
        if self.protocol == "DIGIDIM":
            try:
                self.type = DIGIDIM_TYPES[(h_2_d(*bytes[:-4:-1]))]
            except KeyError:
                _LOGGER.error(
                    f"Encountered unknown DIGIDIM device type of {d_2_h(raw_type)}"
                )
                self.type = DigidimType("0", UNKNOWN_DIGIDIM_TYPE, False)

        # TODO: Decode other device types.


class Devices:
    def __init__(self, router):
        self.router = router
        self.devices = {}

    def register_device(self, device: Device):
        self.devices[device.address] = device

    async def update_device_state(self, address, state):
        await self._update_device_param(address, "state", state)

    async def update_device_load_level(self, address, load_level):
        await self._update_device_param(address, "load_level", float(load_level))

    async def update_device_name(self, address, name):
        await self._update_device_param(address, "name", name)

    def unregister_subscription(self, device_address, func):
        device = self.devices.get(device_address)

        if device:
            device.remove_subscriber(func)
            return True
        return False

    def register_subscription(self, device_address, func):
        device = self.devices.get(device_address)

        if device:
            device.add_subscriber(func)
            return True
        return False

    async def _update_device_param(self, address, param, value):
        _LOGGER.debug(f"Updating {param} on device {address} to {value}")
        try:
            setattr(self.devices[address], param, value)
            await self.devices[address].update_subscribers()
        except KeyError:
            _LOGGER.warn(f"Couldn't find device with address: {address}")
            raise

    def get_light_devices(self):
        return [device for device in self.devices.values() if device.is_light is True]

    def update_device_scene_level(self, address, scene_levels):

        levels = scene_levels.split(",")
        if len(levels) != 136:
            raise ParserError(None, f"Expecting 136 scene levels, got {len(levels)}.")

        self.devices[address].set_scene_levels(levels)

    async def set_device_brightness(self, address, brightness: int, fade_time=100):

        load_level = f"{((brightness/255)*100):.1f}"

        await self.set_device_load_level(address, load_level, fade_time)

    async def set_device_load_level(self, address, load_level: str, fade_time=100):
        _LOGGER.info(
            f"Updating device {address} load level to {load_level} over {fade_time}ms..."
        )

        async def task(devices, address, load_level):
            # Routers don't seem to respond to these messages.
            await devices.router._send_command_task(
                Command(
                    CommandType.DIRECT_LEVEL_DEVICE,
                    [
                        CommandParameter(CommandParameterType.LEVEL, load_level),
                        CommandParameter(CommandParameterType.FADE_TIME, fade_time),
                    ],
                    command_address=address,
                )
            )
            _LOGGER.debug(f"Updated device {address} load level to {load_level}.")

            await devices.update_device_load_level(address, load_level)

            response = await self.router._send_command_task(
                Command(CommandType.QUERY_DEVICE_LOAD_LEVEL, command_address=address)
            )
            await devices.update_device_load_level(address, response.result)

        asyncio.create_task(task(self, address, load_level))

    async def update_device(self, address):
        # Update name, state and load.

        device = self.devices[address]

        async def update_name(device):
            response = await self.router._send_command_task(
                Command(
                    CommandType.QUERY_DEVICE_DESCRIPTION, command_address=device.address
                )
            )
            await self.update_device_name(device.address, response.result)

        async def update_state(device):
            response = await self.router._send_command_task(
                Command(CommandType.QUERY_DEVICE_STATE, command_address=device.address)
            )
            await self.update_device_state(device.address, response.result)

        async def update_load_level(device):
            response = await self.router._send_command_task(
                Command(
                    CommandType.QUERY_DEVICE_LOAD_LEVEL, command_address=device.address
                )
            )
            await self.update_device_load_level(device.address, response.result)

        async def update_scene_level(device):
            response = await self.router._send_command_task(
                Command(CommandType.QUERY_SCENE_INFO, command_address=device.address)
            )
            self.update_device_scene_level(device.address, response.result)

        asyncio.create_task(update_name(device))
        asyncio.create_task(update_state(device))

        if device.is_load:
            asyncio.create_task(update_load_level(device))
            asyncio.create_task(update_scene_level(device))


async def receive_and_register_devices(router, command):

    command = await router._send_command_task(command)
    if command.result is None:
        _LOGGER.info("No devices found.")
        return

    if "@" not in command.result:
        _LOGGER.info(f"Not able to split, '{command.result}' does not contain @")
        return

    device_results = command.result.split(",")
    for device_result in device_results:
        device_type, device_address = device_result.split("@")

        address = copy(command.command_address)
        address.device = device_address

        router.devices.register_device(Device(address, device_type))
        await router.devices.update_device(address)


async def get_devices(router):

    [
        asyncio.create_task(
            receive_and_register_devices(
                router,
                Command(
                    CommandType.QUERY_DEVICE_TYPES_AND_ADDRESSES,
                    command_address=HelvarAddress(
                        router.cluster_id, router.router_id, subnet_id
                    ),
                ),
            )
        )
        for subnet_id in range(1, 5)
    ]
