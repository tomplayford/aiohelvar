from enum import Enum


class CommandParameterType(Enum):
    VERSION = "V"
    COMMAND = "C"
    ADDRESS = "@"
    GROUP = "G"
    SCENE = "S"
    BLOCK = "B"
    FADE_TIME = "F"
    LEVEL = "L"
    PROPORTION = "P"
    DISPLAY_SCREEN = "D"
    SEQUENCE_NUMBER = "Q"
    TIME = "T"
    ACK = "A"
    LATITUDE = "L"
    LONGITUDE = "E"
    TIME_ZONE_DIFFERENCE = "Z"
    DAYLIGHT_SAVING_TIME = "Y"
    CONSTANT_LIGHT_SCENE = "K"
    FORCE_STORE_SCENE = "O"

    def __str__(self):
        return self.value


class CommandParameter:
    def __init__(self, command_parameter_type: CommandParameterType, argument: str):
        self.command_parameter_type = command_parameter_type
        self.argument = argument

    def __str__(self):
        return f"{self.command_parameter_type}:{self.argument}"

    def __eq__(self, o):
        return (self.command_parameter_type, self.argument) == (
            o.command_parameter_type,
            o.argument,
        )
