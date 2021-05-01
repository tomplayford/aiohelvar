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
