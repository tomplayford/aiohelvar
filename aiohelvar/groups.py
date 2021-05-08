from aiohelvar.parser.address import HelvarAddress
import asyncio
from aiohelvar.parser.command_parameter import CommandParameter, CommandParameterType
from .parser.command_type import CommandType
from .parser.command import Command


class Group:
    def __init__(self, group_id, name=None):
        self.group_id = group_id
        self.name = None
        self.devices = []

    def __str__(self):
        return f"Group {self.group_id}: {self.name}. Has {len(self.devices)} devices."

    def __hash__(self) -> int:
        return hash(self.group_id)

    def __eq__(self, o: object) -> bool:
        return self.group_id == o.group_id


class Groups:
    def __init__(self, router):
        self.router = router
        self.groups = {}

    def register_group(self, group):
        self.groups[group.group_id] = group

    def update_group_name(self, group_id, name):
        self.groups[group_id].name = name

    def update_group_device_members(self, group_id, addresses):
        self.groups[group_id].devices = addresses


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

        members = [member.strip("@") for member in response.result.split(",")]

        addresses = [HelvarAddress(*member.split(".")) for member in members]

        router.groups.update_group_device_members(group_id, addresses)

    groups = [Group(group_id) for group_id in response.result.split(",")]

    for group in groups:
        router.groups.register_group(group)
        asyncio.create_task(update_name(router, group.group_id))
        asyncio.create_task(update_group_devices(router, group.group_id))
