from .command_type import CommandType, MessageType
from .command_parameter import CommandParameter, CommandParameterType
from .address import HelvarAddress, SceneAddress
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
        command_parameters: List[CommandParameter] = [],
        command_message_type: MessageType = MessageType.COMMAND,
        command_address: HelvarAddress = None,
        command_result: str = None,
    ):
        self.command_type = command_type
        self.command_parameters = command_parameters
        self.command_message_type = command_message_type
        self.command_address = command_address
        self.result = command_result

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

        if self.result:
            main_message = f"{main_message}={self.result}"

        return f"{self.command_message_type}{main_message}{default_helvar_termination_char}"

    def get_param_value(self, parameter_type: CommandParameterType):
        for parameter in self.command_parameters:
            if parameter.command_parameter_type == parameter_type:
                return parameter.argument
        return None

    def get_scene_address(self):

        group = self.get_param_value(CommandParameterType.GROUP)
        block = self.get_param_value(CommandParameterType.BLOCK)
        scene = self.get_param_value(CommandParameterType.SCENE)

        if group is not None and block is not None and scene is not None:
            return SceneAddress(int(group), int(block), int(scene))
        return None

    @property
    def type_parameters_address(self):

        # return (self.command_type, self.command_parameters, self.command_address)

        parameters = []
        if self.command_address is not None:
            parameters.append(self.command_address)

        result = ",".join([str(p) for p in parameters])
        return f"{self.command_type}:{result}"
