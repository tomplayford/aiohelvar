from aiohelvar.parser.command_type import CommandType, MessageType
from aiohelvar.parser.command_parameter import CommandParameter, CommandParameterType
from aiohelvar.parser.address import HelvarAddress
from typing import List

default_helvarNet_version = "2"
default_helvar_termination_char = "#"


class Command:
    """
    Message Type: Command, internal command, error, response
    Command Type: QUERY_CLUSTERS, DIRECT_LEVEL_DEVICE etc.
    Command Parameters: G:1, S:3 etc.

    """

    def __init__(
        self,
        command_type: CommandType,
        command_parameters: List[CommandParameter],
        command_message_type: MessageType = MessageType.COMMAND,
        command_address: HelvarAddress = None,
    ):
        self.command_type = command_type
        self.command_parameters = command_parameters
        self.command_message_type = command_message_type
        self.command_address = command_address

    def build_base_parameters(self):
        return [
            CommandParameter(CommandParameterType.VERSION, default_helvarNet_version),
            CommandParameter(
                CommandParameterType.COMMAND, self.command_type.command_id
            ),
        ]

    def __str__(self):

        parameters = self.build_base_parameters()

        parameters += self.command_parameters

        if self.command_address is not None:
            parameters.append(self.command_address)

        main_message = ",".join([str(p) for p in parameters])
        return f"{self.command_message_type}{main_message}{default_helvar_termination_char}"
