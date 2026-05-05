from .parser.command_type import MessageType
from .parser.command import Command


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class ParserError(Error):
    """Exception raised for errors in the input.

    Attributes:
        command -- input command in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, command, message):
        self.expression = command
        self.message = message


class UnrecognizedCommand(ParserError):
    """Exception raised when the parser encounters a command it does not recognize"""

    pass


class CommandResponseTimeout(Error):
    """Exception raised when we don't receive a response to a command to the route within
    the allowed timeout."""

    def __init__(self, command):
        self.expression = command


# HelvarNet exceptions
class HelvarNetError(Error):
    error_id: int = -1
    description: str = "Unknown description"

    def __init__(self,error_id: int|None=None):
        if error_id:
            self.error_id = error_id
        super().__init__(f"[{self.error_id}] {self.description}")
    def __str__(self) -> str:
        return f"[{self.error_id}] {self.description}"

class InvalidGroupIndexParameterError(HelvarNetError):
    error_id = 1
    description = "Invalid group index parameter"


class InvalidClusterParameterError(HelvarNetError):
    error_id = 2
    description = "Invalid cluster parameter"


class InvalidRouterParameterError(HelvarNetError):
    error_id = 3
    description = "Invalid router parameter"


class InvalidSubnetParameterError(HelvarNetError):
    error_id = 4
    description = "Invalid subnet parameter"


class InvalidDeviceParameterError(HelvarNetError):
    error_id = 5
    description = "Invalid device parameter"


class InvalidSubDeviceParameterError(HelvarNetError):
    error_id = 6
    description = "Invalid sub device parameter"


class InvalidBlockParameterError(HelvarNetError):
    error_id = 7
    description = "Invalid block parameter"


class InvalidSceneParameterError(HelvarNetError):
    error_id = 8
    description = "Invalid scene parameter"


class ClusterDoesNotExistError(HelvarNetError):
    error_id = 9
    description = "Cluster does not exist"


class RouterDoesNotExistError(HelvarNetError):
    error_id = 10
    description = "Router does not exist"


class DeviceDoesNotExistError(HelvarNetError):
    error_id = 11
    description = "Device does not exist"


class PropertyDoesNotExistError(HelvarNetError):
    error_id = 12
    description = "Property does not exist"


class InvalidRawMessageSizeError(HelvarNetError):
    error_id = 13
    description = "Invalid RAW message size"


class InvalidMessageTypeError(HelvarNetError):
    error_id = 14
    description = "Invalid messages type"


class InvalidMessageCommandError(HelvarNetError):
    error_id = 15
    description = "Invalid message command"


class MissingAsciiTerminatorError(HelvarNetError):
    error_id = 16
    description = "Missing ASCII terminator"


class MissingAsciiParameterError(HelvarNetError):
    error_id = 17
    description = "Missing ASCII parameter"


class IncompatibleVersionError(HelvarNetError):
    error_id = 18
    description = "Incompatible version"


_HELVARNET_ERROR_CLASSES: dict[int, type[HelvarNetError]] = {
    cls.error_id: cls
    for cls in HelvarNetError.__subclasses__()
}

def helvarnet_error_by_result(result: int | str | Command) -> HelvarNetError | None:
    """ Returns a HelvarNetError for a command or a command's error_id.
    Returns None if the command is not an error."""

    if isinstance(result,Command):
        if result.command_message_type != MessageType.ERROR:
            return None
        result = result.result

    result = int(result) # NOTE: can throw ValueError

    ret = _HELVARNET_ERROR_CLASSES.get(result)

    if not ret and result != 0:
        ret = HelvarNetError(error_id=result)
    elif ret:
        ret = ret()

    return ret

if __name__ == "__main__":
    err = helvarnet_error_by_result(1)
    print(f"err: {err}")
    err = helvarnet_error_by_result(0)
    assert err is None, f"Expected None for result 0, got {err}"
    err = helvarnet_error_by_result(9999)
    print(f"err: {err}")
    err = HelvarNetError(error_id=9876)
    err.description = "This is a custom error with an unknown error code."
    raise err