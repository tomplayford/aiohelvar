
from aiohelvar.parser.address import HelvarAddress
from aiohelvar.parser.command_parameter import CommandParameter, CommandParameterType
from .parser.command_type import CommandType
from .parser.command import Command

from copy import copy
import asyncio

class Device:
    def __init__(self, address: HelvarAddress, type=None, name=None):
        self.address = address
        self.name = None
        self.state = None
        self.load_level = None

    def __str__(self):
        return f"Device {self.address}: {self.description}. State: {self.state}. Load: {self.load_level}."

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

    async def update_device(self, address):
        # TODO: refactor to tasks rather than callbacks.
        # Update name, state and load.

        device = self.devices[address]

        response = await self.router.send_command(
            Command(
                CommandType.QUERY_DEVICE_DESCRIPTION,
                command_address=device.address
            )
        )
        response.add_done_callback(lambda task: self.update_device_name(device.address, task.result().result))

        response = await self.router.send_command(
            Command(
                CommandType.QUERY_DEVICE_STATE,
                command_address=device.address
            )
        )
        response.add_done_callback(lambda task: self.update_device_state(device.address, task.result().result))

        response = await self.router.send_command(
            Command(
                CommandType.QUERY_DEVICE_LOAD_LEVEL,
                command_address=device.address
            )
        )
        response.add_done_callback(lambda task: self.update_device_load_level(device.address, task.result().result))


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
