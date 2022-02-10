from aiohelvar.lib import Subscribable
from aiohelvar.static import DEFAULT_FADE_TIME
from aiohelvar.parser.address import HelvarAddress, SceneAddress
import asyncio
from aiohelvar.parser.command_parameter import CommandParameter, CommandParameterType
from .parser.command_type import CommandType, MessageType
from .parser.command import Command

import logging

_LOGGER = logging.getLogger(__name__)


def blockscene_to_block_and_scene(block_scene: int):
    scene = block_scene % 16
    block = ((block_scene - scene) / 16) + 1
    return block, scene + 1


class Group(Subscribable):
    def __init__(self, group_id: int, name=None):
        super(Group, self).__init__()
        self.group_id: int = group_id
        self.name = None
        self.devices = []
        self.last_scene = None

    def __str__(self):
        return f"Group {self.group_id}: {self.name}. Has {len(self.devices)} devices."

    def __hash__(self) -> int:
        return hash(self.group_id)

    def __eq__(self, o: object) -> bool:
        return self.group_id == o.group_id

    def get_levels_for_scene(self, scene_address):
        pass
        # TODO
        # levels = {}

        # for device in self.devices:
        #     levels[device.address] = device.level_for_scene(scene_address)

        # return levels


class Groups:
    def __init__(self, router):
        self.router = router
        self.groups = {}

    def register_group(self, group: Group):
        self.groups[int(group.group_id)] = group

    def update_group_name(self, group_id: int, name):
        self.groups[int(group_id)].name = name

    def update_group_device_members(self, group_id: int, addresses):
        self.groups[int(group_id)].devices = addresses

    def unregister_subscription(self, group_id, func):
        group = self.groups.get(group_id)

        if group:
            group.remove_subscriber(func)
            return True
        return False

    def register_subscription(self, group_id, func):
        group = self.groups.get(group_id)

        if group:
            group.add_subscriber(func)
            return True
        return False

    async def handle_scene_callback(self, scene_address: SceneAddress, fade_time):

        if scene_address.group not in self.groups.keys():
            _LOGGER.info(
                f"Scene {scene_address} not in any known group. Looking for {scene_address.group} in {self.groups.keys()}. Ignoring."
            )
            return

        group = self.groups[scene_address.group]
        group.last_scene = scene_address

        _LOGGER.info(
            f"Updating devices in group {group.name} to scene {scene_address}..."
        )
        for device_address in self.groups[scene_address.group].devices:
            device = self.router.devices.devices.get(device_address)
            if device is None:
                _LOGGER.warning(
                    f"Can't find device {device_address} registered in group {scene_address.group}."
                )
                continue
            await device.set_scene_level(scene_address)

        await group.update_subscribers()

        _LOGGER.info(f"Updated devices in scene {scene_address}.")

    async def set_scene(self, scene_address: SceneAddress, fade_time=DEFAULT_FADE_TIME):
        """Set the scene with the router, we'll get a callback that well use to update device state."""

        await self.router.send_command(
            Command(
                CommandType.RECALL_SCENE,
                [
                    CommandParameter(CommandParameterType.GROUP, scene_address.group),
                    CommandParameter(CommandParameterType.BLOCK, scene_address.block),
                    CommandParameter(CommandParameterType.SCENE, scene_address.scene),
                    CommandParameter(CommandParameterType.FADE_TIME, fade_time),
                ],
            )
        )


async def get_groups(router):

    response = await router._send_command_task(Command(CommandType.QUERY_GROUPS))

    # We expect a comma separated list of group ids.
    async def update_name(router, group_id):
        response = await router._send_command_task(
            Command(
                CommandType.QUERY_GROUP_DESCRIPTION,
                [CommandParameter(CommandParameterType.GROUP, group_id)],
            )
        )
        router.groups.update_group_name(group_id, response.result)

    async def update_group_devices(router, group_id):
        response = await router._send_command_task(
            Command(
                CommandType.QUERY_GROUP,
                [CommandParameter(CommandParameterType.GROUP, group_id)],
            )
        )

        if response.result is not None:
            members = [member.strip("@") for member in response.result.split(",")]
            _LOGGER.debug(f"members is '{members}'")

            addresses = [HelvarAddress(*member.split(".")) for member in members]
            _LOGGER.debug(f"addresses is '{addresses}'")

            router.groups.update_group_device_members(group_id, addresses)

    async def update_group_last_scene(router, group_id):
        response = await router._send_command_task(
            Command(
                CommandType.QUERY_LAST_SCENE_IN_GROUP,
                [CommandParameter(CommandParameterType.GROUP, group_id)],
            )
        )

        if response.command_message_type != MessageType.REPLY:
            if response.command_message_type != MessageType.ERROR:
                _LOGGER.error(f"Error reply to command: {response}")
                return
            _LOGGER.error(f"Unexpected reply to command: {response}")

        block_scene = int(response.result)
        scene_address = SceneAddress(
            group_id, *blockscene_to_block_and_scene(block_scene)
        )
        await router.groups.handle_scene_callback(scene_address, 10)

    groups = [Group(group_id) for group_id in response.result.split(",")]

    for group in groups:
        router.groups.register_group(group)
        asyncio.create_task(update_name(router, group.group_id))
        asyncio.create_task(update_group_devices(router, group.group_id))
        asyncio.create_task(update_group_last_scene(router, group.group_id))
