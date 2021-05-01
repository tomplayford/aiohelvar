
from aiohelvar.parser.command_parameter import CommandParameter, CommandParameterType
from .parser.command_type import CommandType
from .parser.command import Command


class Group:
    def __init__(self, group_id, description=None):
        self.group_id = group_id
        self.description = None

    def __str__(self):
        return f"Group {self.group_id}: {self.description}"


async def create_groups_from_command(router, command: Command):
    assert command.command_type == CommandType.QUERY_GROUPS
    # We expect a comma separated list of group ids. 

    groups = [Group(group_id) for group_id in command.result.split(',')]

    for group in groups:

        response = await router.send_command(
            Command(
                CommandType.QUERY_GROUP_DESCRIPTION, 
                [CommandParameter(CommandParameterType.GROUP, group.group_id)]
            )
        )
        await response
        group.description = response.result().result

    return groups
