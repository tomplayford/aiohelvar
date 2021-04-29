from aiohelvar.parser.command_type import CommandType, MessageType
from aiohelvar.parser.address import HelvarAddress
from aiohelvar.parser.command_parameter import CommandParameter, CommandParameterType
from aiohelvar.parser.command import Command
from aiohelvar.exceptions import UnrecognizedCommand
import re


command_regex = "^(?P<type>[<>?!])V:(?P<version>\\d),C:(?P<command>\\d+),?(?P<params>[^=@#]+)?(?P<address>@[^=#]+)?(=(?P<result>[^=#]+))?#?$"


class CommandParser:

    raw_command = None

    def parse_command(self, input):
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

        return Command(
            command_type, parameters, MessageType(match.group("type")), address
        )

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
            return HelvarAddress(*match.group["address"].replace("@", "").split("."))
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
