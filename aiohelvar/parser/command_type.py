from enum import Enum

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
    DIRECT_LEVEL_DEVICE = (14,"Direct Level, Device")
    RECALL_SCENE = (11, "Recall Scene")


    def __init__(self, code, description):
        self.code = code
        self.description = description


class MessageType(Enum):

    COMMAND = (">")
    INTERNAL_COMMAND = ("<")
    REPLY = ("?")
    ERROR = ("!")


class CommandParameterType(Enum):
    VERSION = ("V")
    COMMAND = ("C")
    ADDRESS = ("@")
    GROUP = ("G")
    SCENE = ("S")
    BLOCK = ("B")
    FADE_TIME = ("F")
    LEVEL = ("L")
    PROPORTION = ("P")
    DISPLAY_SCREEN = ("D")
    SEQUENCE_NUMBER  =("Q")
    TIME = ("T")
    ACK = ("A")
    LATITUDE = ("L")
    LONGITUDE = ("E")
    TIME_ZONE_DIFFERENCE = ("Z")
    DAYLIGHT_SAVING_TIME = ("Y")
    CONSTANT_LIGHT_SCENE = ("K")
    FORCE_STORE_SCENE = ("O")