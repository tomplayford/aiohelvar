from aiohelvar.exceptions import UnrecognizedCommand
from .command_type import CommandType, MessageType
from .address import HelvarAddress
from .command_parameter import CommandParameter, CommandParameterType
from .command import Command

import re


command_regex = r"^(?P<type>[<>?!])V\:(?P<version>\d),C\:(?P<command>\d+),?(?P<params>[^=@#]+)?(?P<address>@[^=#]+)?(=(?P<result>[^#]*))?#?$"


class CommandParser:

    raw_command = None

    def parse_command(self, input: bytes):

        input = input.decode()
        r = re.compile(command_regex)
        match = r.fullmatch(input)

        if match is None:
            raise UnrecognizedCommand(
                input, "Could not locate a valid command in input."
            )

        self.raw_command = input

        address = self.parse_address(match)

        parameters = self.parse_params(match)

        command_type = self.parse_command_type(match)

        result = self.parse_result(match)

        return Command(
            command_type,
            command_parameters=parameters,
            command_message_type=MessageType(match.group("type")),
            command_address=address,
            command_result=result,
        )

    def parse_result(self, match):
        if match.group("result"):
            return match.group("result")
        return None

    def parse_command_type(self, match):
        try:
            return CommandType.get_by_command_id(int(match.group("command")))
        except KeyError:
            raise UnrecognizedCommand(
                self.raw_command,
                f"Did not recognize Command Type: {match.group('command')}",
            )

    def parse_address(self, match):

        if match.group("address"):
            return HelvarAddress(
                *list(map(int, match.group("address").replace("@", "").split(".")))
            )
        return None

    def parse_params(self, match):
        parameters = []

        if match.group("params"):

            params = match.group("params").split(",")

            for param in params:
                parts = param.split(":")
                if len(parts) == 2:
                    try:
                        parameters.append(
                            CommandParameter(CommandParameterType(parts[0]), parts[1])
                        )
                    except ValueError:
                        # logger.debug(f"Unsupported Parameter: {param}")
                        raise UnrecognizedCommand(
                            self.raw_command, f"Unsupported Parameter: {param}"
                        )
                else:
                    # logger.debug("Couldn't identify parameter pair in string: {}", param)
                    raise UnrecognizedCommand(
                        self.raw_command,
                        f"Couldn't identify parameter pair in string: {param}",
                    )

        return parameters
