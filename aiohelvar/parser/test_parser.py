from aiohelvar.parser.command_parameter import CommandParameter, CommandParameterType
from aiohelvar.parser.command import Command, CommandType
from aiohelvar.parser.address import HelvarAddress


# Command tests

def test_basic_command_construction():

    command = Command(
        CommandType.QUERY_CLUSTERS,
        CommandParameter(CommandParameterType.GROUP, "2")
    )

    assert str(command) == ">V:2,C:101,G:2#"

# Address tests

def test_helvar_address_equality():

    a = HelvarAddress(1, 2, 3, 4)
    b = HelvarAddress(1, 2, 3, 4)

    assert a == b, "Address should be equal"


def test_helvar_address_non_equality():

    a = HelvarAddress(1, 3, 3, 4)
    b = HelvarAddress(1, 2, 3, 4)

    assert a != b, "Address should not be equal"


def test_helvar_address_equality_short():

    a = HelvarAddress(1, 2)
    b = HelvarAddress(1, 2)

    assert a == b, "Address should be equal"


def test_helvar_address_non_equality_short():

    a = HelvarAddress(1, 3)
    b = HelvarAddress(1, 2)

    assert a != b, "Address should not be equal"
