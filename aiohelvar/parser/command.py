from enum import Enum
from aiohelvar.parser.command_parameter import CommandParameter

default_helvarNet_version = "2"
default_helvar_termination_char = "#"


class CommandType(Enum):
    # Queries
    QUERY_CLUSTERS = (101, "Query Clusters.")
    QUERY_GROUP_DESCRIPTION = (105, "Query group description.")
    QUERY_DESCRIPTION_DEVICE = (106, "Query device description.")
    QUERY_DEVICE_TYPES_AND_ADDRESSES = (100, "Query Device Types and Addresses")
    QUERY_DEVICE_STATE = (110, "Query Device State")
    QUERY_DEVICE_LOAD_LEVEL = (152, "Query Device Load Level")
    QUERY_SCENE_INFO = (167, "Query device scene levels.")
    QUERY_ROUTER_TIME = (185, "Query Router Time")
    QUERY_LAST_SCENE_IN_GROUP = (109, "Query last scene selected in a group.")
    QUERY_LAST_SCENE_IN_BLOCK = (103, "Query last scene selected in a group block.")
    QUERY_GROUP = (164, "Query devices in group.")
    QUERY_GROUPS = (165, "Query all groups.")
    QUERY_SCENE_NAMES = (166, "Query all scene names in group.")
    # Commands
    DIRECT_LEVEL_DEVICE = (14, "Direct Level, Device")
    RECALL_SCENE = (11, "Recall Scene")

    def __init__(self, command_id: int, command_name: str):
        self.command_id = command_id
        self.command_name = command_name


class CommandMessageType(Enum):
    COMMAND = ">"
    INTERNAL_COMMAND = "<"
    REPLY = "?"
    ERROR = "!"


class Command:
    def __init__(
        self,
        command_type: CommandType,
        command_parameter: CommandParameter,
        command_message_type: CommandMessageType = CommandMessageType.COMMAND,
    ):
        self.command_type = command_type
        self.command_parameter = command_parameter
        self.command_message_type = command_message_type
