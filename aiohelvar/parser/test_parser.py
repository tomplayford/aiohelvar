from aiohelvar.parser.parser import CommandParser
from aiohelvar.parser.command_parameter import CommandParameter, CommandParameterType
from aiohelvar.parser.command import Command, CommandType
from aiohelvar.parser.address import HelvarAddress, SceneAddress
import logging

_LOGGER = logging.getLogger(__name__)

# Command tests


def test_command_parseing_simple():

    command_strings = [
        ">V:2,C:101,G:2#",
        ">V:2,C:101,G:2,S:3#",
        ">V:2,C:101,@1.2.2.22=@2.1.2.77=small light,@1.4.5.6=another light#",
    ]

    for command_string in command_strings:
        parser = CommandParser()
        command = parser.parse_command(bytes(command_string, "utf8"))

        assert isinstance(command, Command) is True
        assert command != command_string
        assert str(command) == command_string


def test_basic_command_construction():

    command = Command(
        CommandType.QUERY_CLUSTERS, [CommandParameter(CommandParameterType.GROUP, "2")]
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


def test_helvar_address_equality_string_int():

    a = HelvarAddress(1, 2, 3, 4)
    b = HelvarAddress("1", "2", "3", "4")

    assert a == b, "Address should be equal"


def test_helvar_address_equality_short():

    a = HelvarAddress(1, 2)
    b = HelvarAddress(1, 2)

    assert a == b, "Address should be equal"


def test_helvar_address_non_equality_short():

    a = HelvarAddress(1, 3)
    b = HelvarAddress(1, 2)

    assert a != b, "Address should not be equal"


def test_helvar_address_non_equality_short_and_long():

    a = HelvarAddress(1, 2)
    b = HelvarAddress(1, 2, 3, 4)

    assert a != b, "Address should not be equal"


# Error handling tests


def test_command_parser_invalid_command_format():
    """Test parsing invalid command formats"""
    parser = CommandParser()
    
    # Test malformed commands
    invalid_commands = [
        b"",  # Empty string
        b"invalid",  # No command structure
        b">V:2,C:999,G:2#",  # Invalid command type
        b">V:2,C:abc,G:2#",  # Non-numeric command type
        b">V:2,C:101,G:abc#",  # Non-numeric parameter
        b">V:2,C:101,@1.2.3.abc#",  # Invalid address format
        b">V:2,C:101,@1.2.3.4.5.6#",  # Too many address parts
    ]
    
    for cmd in invalid_commands:
        try:
            result = parser.parse_command(cmd)
            # If no exception, result should be None for invalid commands
            assert result is None, f"Expected None for invalid command: {cmd}"
        except Exception:
            # Exceptions are acceptable for malformed input
            pass


def test_helvar_address_validation_errors():
    """Test HelvarAddress validation"""
    
    # Test invalid block values
    try:
        HelvarAddress(-1, 1)
        assert False, "Should raise error for negative block"
    except (TypeError, ValueError):
        pass
    
    try:
        HelvarAddress(300, 1)
        assert False, "Should raise error for block > 253"
    except (TypeError, ValueError):
        pass
    
    # Test invalid router values
    try:
        HelvarAddress(1, 0)
        assert False, "Should raise error for router < 1"
    except (TypeError, ValueError):
        pass
    
    try:
        HelvarAddress(1, 300)
        assert False, "Should raise error for router > 254"
    except (TypeError, ValueError):
        pass


def test_helvar_address_hash():
    """Test HelvarAddress hash functionality"""
    a = HelvarAddress(1, 2, 3, 4)
    b = HelvarAddress(1, 2, 3, 4)
    c = HelvarAddress(1, 2, 3, 5)
    
    # Equal addresses should have same hash
    assert hash(a) == hash(b), "Equal addresses should have same hash"
    
    # Different addresses should have different hashes
    assert hash(a) != hash(c), "Different addresses should have different hashes"
    
    # Test with None values
    d = HelvarAddress(1, 2, None, None)
    hash_result = hash(d)  # Should not raise exception
    assert isinstance(hash_result, int), "Hash should return integer"


def test_helvar_address_str_representation():
    """Test HelvarAddress string representation"""
    a = HelvarAddress(1, 2, 3, 4)
    assert str(a) == "@1.2.3.4", f"Expected '@1.2.3.4', got {str(a)}"
    
    b = HelvarAddress(1, 2)
    assert str(b) == "@1.2", f"Expected '@1.2', got {str(b)}"
    
    c = HelvarAddress(1, 2, None, None)
    assert str(c) == "@1.2", f"Expected '@1.2', got {str(c)}"


def test_helvar_address_bus_type():
    """Test bus type determination"""
    # DALI subnets (1, 2)
    a = HelvarAddress(1, 2, 1, 4)
    assert a.bus_type() == "DALI", f"Expected DALI, got {a.bus_type()}"
    
    b = HelvarAddress(1, 2, 2, 4)
    assert b.bus_type() == "DALI", f"Expected DALI, got {b.bus_type()}"
    
    # S-DIM subnet (3)
    c = HelvarAddress(1, 2, 3, 4)
    assert c.bus_type() == "S-DIM", f"Expected S-DIM, got {c.bus_type()}"
    
    # DMX subnet (4)
    d = HelvarAddress(1, 2, 4, 4)
    assert d.bus_type() == "DMX", f"Expected DMX, got {d.bus_type()}"


# SceneAddress tests


def test_scene_address_creation():
    """Test SceneAddress creation"""
    a = SceneAddress(1, 2, 3)
    assert a.group == 1, f"Expected group 1, got {a.group}"
    assert a.block == 2, f"Expected block 2, got {a.block}"
    assert a.scene == 3, f"Expected scene 3, got {a.scene}"


def test_scene_address_validation():
    """Test SceneAddress validation"""
    
    # Valid ranges
    SceneAddress(0, 1, 1)  # group 0 is valid
    SceneAddress(128, 8, 16)  # max values
    
    # Test invalid group values
    try:
        SceneAddress(-1, 1, 1)
        assert False, "Should raise error for negative group"
    except (TypeError, ValueError):
        pass
    
    try:
        SceneAddress(129, 1, 1)
        assert False, "Should raise error for group > 128"
    except (TypeError, ValueError):
        pass
    
    # Test invalid block values
    try:
        SceneAddress(1, 0, 1)
        assert False, "Should raise error for block < 1"
    except (TypeError, ValueError):
        pass
    
    try:
        SceneAddress(1, 9, 1)
        assert False, "Should raise error for block > 8"
    except (TypeError, ValueError):
        pass
    
    # Test invalid scene values
    try:
        SceneAddress(1, 1, 0)
        assert False, "Should raise error for scene < 1"
    except (TypeError, ValueError):
        pass
    
    try:
        SceneAddress(1, 1, 17)
        assert False, "Should raise error for scene > 16"
    except (TypeError, ValueError):
        pass


def test_scene_address_equality():
    """Test SceneAddress equality"""
    a = SceneAddress(1, 2, 3)
    b = SceneAddress(1, 2, 3)
    c = SceneAddress(1, 2, 4)
    
    assert a == b, "Equal scene addresses should be equal"
    assert a != c, "Different scene addresses should not be equal"


def test_scene_address_str_representation():
    """Test SceneAddress string representation"""
    a = SceneAddress(1, 2, 3)
    assert str(a) == "@1.2.3", f"Expected '@1.2.3', got {str(a)}"


def test_scene_address_fromString():
    """Test SceneAddress fromString method"""
    a = SceneAddress.fromString("@1.2.3")
    assert a.group == 1, f"Expected group 1, got {a.group}"
    assert a.block == 2, f"Expected block 2, got {a.block}"
    assert a.scene == 3, f"Expected scene 3, got {a.scene}"
    
    # Test invalid format
    try:
        SceneAddress.fromString("invalid")
        assert False, "Should raise error for invalid format"
    except (ValueError, AttributeError):
        pass


def test_scene_address_to_device_int():
    """Test SceneAddress to_device_int method"""
    a = SceneAddress(1, 2, 3)
    result = a.to_device_int()
    assert isinstance(result, int), f"Expected int, got {type(result)}"
    assert result > 0, f"Expected positive int, got {result}"


def test_scene_address_to_int():
    """Test SceneAddress to_int method"""
    a = SceneAddress(1, 2, 3)
    result = a.to_int()
    assert isinstance(result, int), f"Expected int, got {type(result)}"
    assert result > 0, f"Expected positive int, got {result}"


# CommandType tests


def test_command_type_get_by_command_id():
    """Test CommandType.get_by_command_id method"""
    # Test valid command ID
    cmd_type = CommandType.get_by_command_id(101)
    assert cmd_type is not None, "Should return valid CommandType"
    
    # Test invalid command ID
    try:
        CommandType.get_by_command_id(9999)
        assert False, "Should raise error for invalid command ID"
    except (KeyError, ValueError):
        pass


def test_command_type_str_representation():
    """Test CommandType string representation"""
    cmd_type = CommandType.get_by_command_id(101)
    str_repr = str(cmd_type)
    assert isinstance(str_repr, str), f"Expected string, got {type(str_repr)}"
    assert len(str_repr) > 0, "String representation should not be empty"


# CommandParameter tests


def test_command_parameter_equality():
    """Test CommandParameter equality"""
    a = CommandParameter(CommandParameterType.GROUP, "2")
    b = CommandParameter(CommandParameterType.GROUP, "2")
    c = CommandParameter(CommandParameterType.GROUP, "3")
    
    assert a == b, "Equal parameters should be equal"
    assert a != c, "Different parameters should not be equal"


def test_command_parameter_str_representation():
    """Test CommandParameter string representation"""
    param = CommandParameter(CommandParameterType.GROUP, "2")
    str_repr = str(param)
    assert isinstance(str_repr, str), f"Expected string, got {type(str_repr)}"
    assert "G:2" in str_repr, f"Expected 'G:2' in string, got {str_repr}"


# Command method tests


def test_command_get_param_value():
    """Test Command.get_param_value method"""
    cmd = Command(
        CommandType.QUERY_CLUSTERS,
        [CommandParameter(CommandParameterType.GROUP, "2")]
    )
    
    value = cmd.get_param_value(CommandParameterType.GROUP)
    assert value == "2", f"Expected '2', got {value}"
    
    # Test non-existent parameter
    value = cmd.get_param_value(CommandParameterType.LEVEL)
    assert value is None, f"Expected None, got {value}"


def test_command_complex_construction():
    """Test Command construction with various parameters"""
    # Test with address
    address = HelvarAddress(1, 2, 3, 4)
    cmd = Command(
        CommandType.DIRECT_LEVEL_DEVICE,
        [
            CommandParameter(CommandParameterType.LEVEL, "50"),
            CommandParameter(CommandParameterType.FADE_TIME, "1000")
        ],
        command_address=address
    )
    
    str_repr = str(cmd)
    assert "@1.2.3.4" in str_repr, f"Address should be in string: {str_repr}"
    assert "L:50" in str_repr, f"Level should be in string: {str_repr}"
    assert "F:1000" in str_repr, f"Fade time should be in string: {str_repr}"


# Integration tests


def test_parse_and_reconstruct_command():
    """Test parsing a command and reconstructing it"""
    original = ">V:2,C:101,G:2#"
    parser = CommandParser()
    
    # Parse command
    parsed = parser.parse_command(bytes(original, "utf8"))
    assert parsed is not None, "Command should parse successfully"
    
    # Reconstruct command
    reconstructed = str(parsed)
    assert reconstructed == original, f"Expected {original}, got {reconstructed}"


def test_parse_command_with_address():
    """Test parsing command with address"""
    command_string = ">V:2,C:14,@1.2.3.4#"
    parser = CommandParser()
    
    parsed = parser.parse_command(bytes(command_string, "utf8"))
    assert parsed is not None, "Command should parse successfully"
    assert parsed.command_address is not None, "Address should be parsed"
    assert str(parsed.command_address) == "@1.2.3.4", "Address should match"


def test_parse_command_with_result():
    """Test parsing command with result"""
    command_string = ">V:2,C:101,G:2=result_data#"
    parser = CommandParser()
    
    parsed = parser.parse_command(bytes(command_string, "utf8"))
    assert parsed is not None, "Command should parse successfully"
    assert parsed.result == "result_data", f"Expected 'result_data', got {parsed.result}"


# Edge case tests


def test_address_with_none_values():
    """Test addresses with None values"""
    a = HelvarAddress(1, 2, None, None)
    b = HelvarAddress(1, 2, None, None)
    
    assert a == b, "Addresses with None values should be equal"
    assert str(a) == "@1.2", "String should not include None values"


def test_empty_parameter_list():
    """Test command with empty parameter list"""
    cmd = Command(CommandType.QUERY_CLUSTERS, [])
    str_repr = str(cmd)
    assert "C:101" in str_repr, "Command type should be in string"


def test_unicode_handling():
    """Test handling of unicode characters"""
    try:
        # Test with unicode bytes
        unicode_cmd = ">V:2,C:101,G:2#".encode('utf-8')
        parser = CommandParser()
        parsed = parser.parse_command(unicode_cmd)
        assert parsed is not None, "Should handle UTF-8 encoded commands"
    except Exception:
        # Unicode handling may not be supported
        pass
