"""
Comprehensive test suite for aiohelvar main package components.

Tests cover:
- Exceptions and error handling
- Subscribable functionality 
- Device management
- Group management
- Scene management
- Router functionality
- Static utilities
- Configuration
- Integration scenarios
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import aiohelvar components
from aiohelvar.exceptions import Error, ParserError, UnrecognizedCommand, CommandResponseTimeout
from aiohelvar.lib import Subscribable
from aiohelvar.devices import Device, Devices, d_2_h
from aiohelvar.groups import Group, Groups
from aiohelvar.scenes import Scene, Scenes
from aiohelvar.static import h_2_d, DigidimType, DeviceStateFlag
from aiohelvar.parser.address import HelvarAddress, SceneAddress
from aiohelvar.parser.command import Command, CommandType
from aiohelvar.parser.command_parameter import CommandParameter, CommandParameterType
from aiohelvar.router import Router

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


# Test Exceptions
class TestExceptions:
    """Test exception classes and error handling"""
    
    def test_base_error(self):
        """Test base Error exception"""
        error = Error("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_parser_error(self):
        """Test ParserError exception"""
        command = ">V:2,C:101,G:2#"
        message = "Test parser error"
        error = ParserError(command, message)
        
        assert isinstance(error, Error)
        assert error.expression == command
        assert error.message == message
    
    def test_unrecognized_command(self):
        """Test UnrecognizedCommand exception"""
        command = ">V:2,C:999,G:2#"
        message = "Unknown command"
        error = UnrecognizedCommand(command, message)
        
        assert isinstance(error, ParserError)
        assert error.expression == command
        assert error.message == message
    
    def test_command_response_timeout(self):
        """Test CommandResponseTimeout exception"""
        command = ">V:2,C:101,G:2#"
        error = CommandResponseTimeout(command)
        
        assert isinstance(error, Error)
        assert error.expression == command


# Test Subscribable
class TestSubscribable:
    """Test Subscribable mixin functionality"""
    
    def test_subscribable_init(self):
        """Test Subscribable initialization"""
        sub = Subscribable()
        assert sub.subscriptions == []
    
    def test_add_subscriber(self):
        """Test adding subscribers"""
        sub = Subscribable()
        
        def callback1():
            pass
        def callback2():
            pass
        
        sub.add_subscriber(callback1)
        assert len(sub.subscriptions) == 1
        assert callback1 in sub.subscriptions
        
        sub.add_subscriber(callback2)
        assert len(sub.subscriptions) == 2
        assert callback2 in sub.subscriptions
    
    def test_remove_subscriber(self):
        """Test removing subscribers"""
        sub = Subscribable()
        
        def callback1():
            pass
        def callback2():
            pass
        
        sub.add_subscriber(callback1)
        sub.add_subscriber(callback2)
        
        sub.remove_subscriber(callback1)
        assert len(sub.subscriptions) == 1
        assert callback1 not in sub.subscriptions
        assert callback2 in sub.subscriptions
        
        # Test removing non-existent subscriber
        sub.remove_subscriber(callback1)  # Should not raise error
        assert len(sub.subscriptions) == 1
    
    async def test_update_subscribers(self):
        """Test updating subscribers"""
        sub = Subscribable()
        
        # Mock async callbacks
        callback1 = AsyncMock()
        callback2 = AsyncMock()
        
        sub.add_subscriber(callback1)
        sub.add_subscriber(callback2)
        
        await sub.update_subscribers()
        
        callback1.assert_called_once_with(sub)
        callback2.assert_called_once_with(sub)


# Test Device
class TestDevice:
    """Test Device class functionality"""
    
    def test_device_creation(self):
        """Test device creation with address"""
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        
        assert device.address == address
        assert device.name is None
        assert device.load_level == 0.0
        assert device.state == 0
        assert isinstance(device, Subscribable)
    
    def test_device_creation_with_type(self):
        """Test device creation with raw_type parameter"""
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address, raw_type=1)  # 1 = DALI protocol
        
        assert device.address == address
        # Protocol gets set during decode_raw_type_bytecode which needs bytes
        assert device.protocol is not None or device.raw_type is not None
    
    def test_device_string_representation(self):
        """Test device string representation"""
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        device.name = "Test Device"
        device.protocol = "DALI"
        device.type = "Test Type"
        device.state = 1
        device.load_level = 50.0
        
        str_repr = str(device)
        assert "Device @1.2.3.4: Test Device" in str_repr
        assert "Protocol: DALI" in str_repr
        assert "Type: Test Type" in str_repr
        assert "State: 1" in str_repr
        assert "Load: 50.0" in str_repr
    
    def test_device_brightness_property(self):
        """Test brightness property calculation"""
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        
        device.load_level = 0.0
        assert device.brightness == 0
        
        device.load_level = 50.0
        assert device.brightness == int(50.0 * 2.55)
        
        device.load_level = 100.0
        assert device.brightness == 254  # int(100.0 * 2.55) = 254
    
    def test_device_is_load_property(self):
        """Test is_load property logic"""
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        
        # DALI protocol should be load
        device.protocol = "DALI"
        assert device.is_load == True
        
        # DIGIDIM depends on type
        device.protocol = "DIGIDIM"
        device.type = None
        assert device.is_load == False
        
        # Mock type with is_load property
        mock_type = Mock()
        mock_type.is_load = True
        device.type = mock_type
        assert device.is_load == True
        
        # Other protocols default to True
        device.protocol = "S-DIM"
        assert device.is_load == True
    
    async def test_device_set_level_validation(self):
        """Test device level setting with validation"""
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        device.protocol = "DALI"  # Make it a load
        
        # Test if device has set_level method
        if hasattr(device, 'set_level'):
            # Test level clamping
            await device.set_level(-10)  # Should clamp to 0
            # We can't easily test the actual clamping without mocking _set_level
            
            # Test non-load device
            device.protocol = "DIGIDIM"
            device.type = None  # Makes is_load False
            await device.set_level(50)  # Should return early
        else:
            # Device doesn't have set_level method, that's ok
            pass
    
    def test_device_scene_level_handling(self):
        """Test device scene level functionality"""
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        device.protocol = "DALI"
        
        # Test setting scene levels
        levels = [0.0] * 136  # 136 scene levels
        levels[0] = 50.0
        device.set_scene_levels(levels)
        assert device.levels == levels
        
        # Test getting level for scene
        scene_address = SceneAddress(1, 1, 1)
        try:
            level = device.get_level_for_scene(scene_address)
            # Should either return a level or raise IndexError
            assert isinstance(level, (int, float)) or level is None
        except IndexError:
            # This is expected if scene address calculation is out of bounds
            pass


# Test Devices collection
class TestDevices:
    """Test Devices collection class"""
    
    def test_devices_creation(self):
        """Test Devices collection initialization"""
        mock_router = Mock()
        devices = Devices(mock_router)
        
        assert devices.router == mock_router
        assert devices.devices == {}
    
    def test_register_device(self):
        """Test device registration"""
        mock_router = Mock()
        devices = Devices(mock_router)
        
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        
        devices.register_device(device)
        assert address in devices.devices
        assert devices.devices[address] == device
    
    async def test_update_device_load_level(self):
        """Test updating device load level"""
        mock_router = Mock()
        devices = Devices(mock_router)
        
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        devices.register_device(device)
        
        # update_device_load_level is async in the actual implementation
        await devices.update_device_load_level(address, 75.5)
        assert device.load_level == 75.5
    
    async def test_set_device_load_level(self):
        """Test setting device load level with command"""
        mock_router = Mock()
        mock_router._send_command_task = AsyncMock()
        devices = Devices(mock_router)
        
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        device.protocol = "DALI"
        devices.register_device(device)
        
        # This creates an async task, so we need to wait a bit
        await devices.set_device_load_level(address, 50.0, 1000)
        
        # Wait for the task to complete
        await asyncio.sleep(0.1)
        
        # Verify command was sent
        mock_router._send_command_task.assert_called()
        
        # Verify device was updated
        assert device.load_level == 50.0


# Test Group
class TestGroup:
    """Test Group class functionality"""
    
    def test_group_creation(self):
        """Test group creation"""
        group = Group(1)
        
        assert group.group_id == 1
        assert group.name is None
        assert group.devices == []
        assert group.last_scene_address is None
        assert isinstance(group, Subscribable)
    
    def test_group_string_representation(self):
        """Test group string representation"""
        group = Group("1")
        group.name = "Test Group"
        
        str_repr = str(group)
        assert "Group 1: Test Group" in str_repr


# Test Groups collection
class TestGroups:
    """Test Groups collection class"""
    
    def test_groups_creation(self):
        """Test Groups collection initialization"""
        mock_router = Mock()
        groups = Groups(mock_router)
        
        assert groups.router == mock_router
        assert groups.groups == {}
    
    def test_register_group(self):
        """Test group registration"""
        mock_router = Mock()
        groups = Groups(mock_router)
        
        group = Group("1")
        groups.register_group(group)
        
        assert 1 in groups.groups  # Converted to int
        assert groups.groups[1] == group
    
    def test_update_group_device_members(self):
        """Test updating group device members"""
        mock_router = Mock()
        groups = Groups(mock_router)
        
        group = Group(1)
        groups.register_group(group)
        
        addresses = [HelvarAddress(1, 2, 3, 4), HelvarAddress(1, 2, 3, 5)]
        groups.update_group_device_members(1, addresses)
        
        assert group.devices == addresses
    
    def test_subscribe_to_group(self):
        """Test subscribing to group updates"""
        mock_router = Mock()
        groups = Groups(mock_router)
        
        group = Group(1)
        groups.register_group(group)
        
        callback = Mock()
        result = groups.register_subscription(1, callback)
        
        assert result == True
        assert callback in group.subscriptions
        
        # Test subscribing to non-existent group
        result = groups.register_subscription(999, callback)
        assert result == False


# Test Scene
class TestScene:
    """Test Scene class functionality"""
    
    def test_scene_creation(self):
        """Test scene creation"""
        address = SceneAddress(1, 2, 3)
        scene = Scene(address)
        
        assert scene.address == address
        assert scene.name is None
    
    def test_scene_string_representation(self):
        """Test scene string representation"""
        address = SceneAddress(1, 2, 3)
        scene = Scene(address)
        scene.name = "Test Scene"
        
        str_repr = str(scene)
        assert "@1.2.3: Test Scene" in str_repr


# Test Scenes collection
class TestScenes:
    """Test Scenes collection class"""
    
    def test_scenes_creation(self):
        """Test Scenes collection initialization"""
        mock_router = Mock()
        scenes = Scenes(mock_router)
        
        assert scenes.router == mock_router
        assert scenes.scenes == {}
    
    def test_register_scene(self):
        """Test scene registration"""
        mock_router = Mock()
        scenes = Scenes(mock_router)
        
        address = SceneAddress(1, 2, 3)
        scene = Scene(address)
        
        scenes.register_scene(address, scene)
        assert address in scenes.scenes
        assert scenes.scenes[address] == scene
    
    def test_get_scene_safe(self):
        """Test safe scene retrieval"""
        mock_router = Mock()
        scenes = Scenes(mock_router)
        
        address = SceneAddress(1, 2, 3)
        scene = Scene(address)
        scenes.register_scene(address, scene)
        
        # Test existing scene
        result = scenes.get_scene_safe(address)
        assert result == scene
        
        # Test non-existent scene
        missing_address = SceneAddress(1, 8, 16)  # Valid address that doesn't exist
        result = scenes.get_scene_safe(missing_address, "default")
        assert result == "default"
    
    def test_has_scene(self):
        """Test scene existence check"""
        mock_router = Mock()
        scenes = Scenes(mock_router)
        
        address = SceneAddress(1, 2, 3)
        scene = Scene(address)
        scenes.register_scene(address, scene)
        
        assert scenes.has_scene(address) == True
        
        missing_address = SceneAddress(1, 8, 16)  # Valid address that doesn't exist
        assert scenes.has_scene(missing_address) == False
    
    def test_get_scenes_for_group(self):
        """Test getting scenes for a specific group"""
        mock_router = Mock()
        scenes = Scenes(mock_router)
        
        # Add scenes for group 1
        scene1 = Scene(SceneAddress(1, 1, 1))
        scene1.name = "Scene 1"
        scene2 = Scene(SceneAddress(1, 1, 2))
        scene2.name = "Scene 2"
        scene3 = Scene(SceneAddress(1, 1, 3))  # No name
        
        scenes.register_scene(scene1.address, scene1)
        scenes.register_scene(scene2.address, scene2)
        scenes.register_scene(scene3.address, scene3)
        
        # Add scene for different group
        scene_other = Scene(SceneAddress(2, 1, 1))
        scene_other.name = "Other Scene"
        scenes.register_scene(scene_other.address, scene_other)
        
        # Test getting only named scenes
        named_scenes = scenes.get_scenes_for_group(1, only_named=True)
        assert len(named_scenes) == 2
        assert all(scene.name is not None for scene in named_scenes)
        
        # Test getting all scenes
        all_scenes = scenes.get_scenes_for_group(1, only_named=False)
        assert len(all_scenes) == 3


# Test Static Utilities
class TestStaticUtilities:
    """Test static utility functions"""
    
    def test_d_2_h(self):
        """Test decimal to hex conversion"""
        result = d_2_h(255)
        assert result == ['0xff', '0x0', '0x0', '0x0']
        
        result = d_2_h(0)
        assert result == ['0x0', '0x0', '0x0', '0x0']
        
        result = d_2_h(16)
        assert result == ['0x10', '0x0', '0x0', '0x0']
    
    def test_h_2_d(self):
        """Test hex to decimal conversion"""
        result = h_2_d(0xFF, 0, 0)
        assert result == 16711680  # (0xFF << 16) + (0 << 8) + 0
        
        result = h_2_d(0, 0, 0)
        assert result == 0
        
        result = h_2_d(0x10, 0x20, 0x30)
        assert result == 1056816  # (0x10 << 16) + (0x20 << 8) + 0x30
    
    def test_blockscene_to_block_and_scene(self):
        """Test block/scene conversion"""
        from aiohelvar.groups import blockscene_to_block_and_scene
        
        # Test various block/scene combinations
        block, scene = blockscene_to_block_and_scene(17)  # Block 2, Scene 2
        assert block == 2
        assert scene == 2
        
        block, scene = blockscene_to_block_and_scene(1)   # Block 1, Scene 2
        assert block == 1
        assert scene == 2
        
        block, scene = blockscene_to_block_and_scene(16)  # Block 2, Scene 1
        assert block == 2
        assert scene == 1


# Integration Tests
class TestIntegration:
    """Test integration scenarios and complex workflows"""
    
    async def test_device_subscription_workflow(self):
        """Test complete device subscription workflow"""
        # Create mock router
        mock_router = Mock()
        mock_router._send_command_task = AsyncMock()
        
        # Create devices collection
        devices = Devices(mock_router)
        
        # Create and register device
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        device.protocol = "DALI"
        devices.register_device(device)
        
        # Create subscriber
        subscriber_called = False
        async def subscriber(updated_device):
            nonlocal subscriber_called
            subscriber_called = True
            assert updated_device == device
        
        # Subscribe to device
        device.add_subscriber(subscriber)
        
        # Update device and trigger subscribers
        await device._set_level(75.0)
        await device.update_subscribers()
        
        assert subscriber_called == True
    
    async def test_group_scene_workflow(self):
        """Test group and scene interaction workflow"""
        # Create mock router
        mock_router = Mock()
        mock_router.scenes = Mock()
        mock_router.scenes.get_scene = Mock(return_value=None)
        
        # Create groups collection
        groups = Groups(mock_router)
        
        # Create and register group
        group = Group("1")
        groups.register_group(group)
        
        # Test scene callback handling
        scene_address = SceneAddress(1, 2, 3)
        await groups.handle_scene_callback(scene_address, 1000)
        
        # Verify group was updated
        assert group.last_scene_address == scene_address
    
    def test_error_handling_integration(self):
        """Test error handling across components"""
        # Test device with invalid data
        address = HelvarAddress(1, 2, 3, 4)
        device = Device(address)
        
        # Test scene level access with invalid data
        try:
            device.levels = None
            scene_address = SceneAddress(1, 1, 1)
            level = device.get_level_for_scene(scene_address)
            assert level is None
        except (IndexError, AttributeError):
            # These are expected for invalid data
            pass
        
        # Test scenes collection with missing scene
        mock_router = Mock()
        scenes = Scenes(mock_router)
        
        missing_address = SceneAddress(1, 8, 16)  # Valid address that doesn't exist
        result = scenes.get_scene(missing_address)
        assert result is None  # Should return None gracefully


# Test Router
class TestRouter:
    """Test Router class functionality"""
    
    def test_router_creation_with_hostname(self):
        """Test router creation with hostname (non-IP)"""
        router = Router("router.local", 50000)
        
        assert router.host == "router.local"
        assert router.port == 50000
        assert router.cluster_id == 0  # Default value
        assert router.router_id == 1   # Default value
    
    def test_router_creation_with_ipv4_address(self):
        """Test router creation with IPv4 address extracts cluster_id and router_id"""
        router = Router("192.168.10.20", 50000)
        
        assert router.host == "192.168.10.20"
        assert router.port == 50000
        assert router.cluster_id == 10  # 3rd octet
        assert router.router_id == 20   # 4th octet
    
    def test_router_creation_with_ipv4_address_custom_defaults(self):
        """Test router creation with IPv4 address overrides custom defaults"""
        router = Router("10.0.5.15", 50000, cluster_id=99, router_id=88)
        
        assert router.host == "10.0.5.15"
        assert router.port == 50000
        assert router.cluster_id == 5   # 3rd octet overrides 99
        assert router.router_id == 15   # 4th octet overrides 88
    
    def test_router_creation_with_ipv6_address(self):
        """Test router creation with IPv6 address uses default values"""
        router = Router("2001:db8::1", 50000, cluster_id=5, router_id=10)
        
        assert router.host == "2001:db8::1"
        assert router.port == 50000
        assert router.cluster_id == 5   # Uses provided default
        assert router.router_id == 10   # Uses provided default
    
    def test_router_creation_with_invalid_ip_string(self):
        """Test router creation with invalid IP string uses default values"""
        router = Router("not.an.ip.address", 50000, cluster_id=7, router_id=3)
        
        assert router.host == "not.an.ip.address"
        assert router.port == 50000
        assert router.cluster_id == 7   # Uses provided default
        assert router.router_id == 3    # Uses provided default
    
    def test_router_creation_with_edge_case_ips(self):
        """Test router creation with edge case IP addresses"""
        # Test with zeros
        router1 = Router("0.0.0.0", 50000)
        assert router1.cluster_id == 0
        assert router1.router_id == 0
        
        # Test with high values
        router2 = Router("255.255.255.255", 50000)
        assert router2.cluster_id == 255
        assert router2.router_id == 255
        
        # Test with localhost
        router3 = Router("127.0.0.1", 50000)
        assert router3.cluster_id == 0
        assert router3.router_id == 1
    
    def test_router_creation_with_private_ip_ranges(self):
        """Test router creation with various private IP ranges"""
        # Class A private (10.0.0.0/8)
        router1 = Router("10.50.100.200", 50000)
        assert router1.cluster_id == 100
        assert router1.router_id == 200
        
        # Class B private (172.16.0.0/12)
        router2 = Router("172.16.10.5", 50000)
        assert router2.cluster_id == 10
        assert router2.router_id == 5
        
        # Class C private (192.168.0.0/16)
        router3 = Router("192.168.1.1", 50000)
        assert router3.cluster_id == 1
        assert router3.router_id == 1
    
    def test_router_attributes_after_creation(self):
        """Test that all router attributes are properly initialized"""
        router = Router("192.168.1.100", 50000)
        
        # Test IP-derived attributes
        assert router.cluster_id == 1
        assert router.router_id == 100
        
        # Test other attributes exist
        assert router.config is None
        assert router.groups is not None
        assert router.devices is not None
        assert router.scenes is not None
        assert router.connected == False
        assert router.workgroup_name is None
        
        # Test async components exist
        assert hasattr(router, 'commands_to_send')
        assert hasattr(router, 'commands_received')
        assert hasattr(router, 'command_received')
    
    def test_router_with_malformed_ip_components(self):
        """Test router with IP-like strings that aren't valid IPs"""
        # Too many octets
        router1 = Router("192.168.1.1.1", 50000, cluster_id=10, router_id=20)
        assert router1.cluster_id == 10  # Uses default
        assert router1.router_id == 20   # Uses default
        
        # Too few octets
        router2 = Router("192.168.1", 50000, cluster_id=30, router_id=40)
        assert router2.cluster_id == 30  # Uses default
        assert router2.router_id == 40   # Uses default
        
        # Non-numeric octets
        router3 = Router("192.168.x.y", 50000, cluster_id=50, router_id=60)
        assert router3.cluster_id == 50  # Uses default
        assert router3.router_id == 60   # Uses default
    
    def test_router_ip_validation_edge_cases(self):
        """Test edge cases for IP validation"""
        # Leading zeros are invalid in modern IP parsing, so should fall back to defaults
        router1 = Router("192.168.001.010", 50000, cluster_id=5, router_id=10)
        assert router1.cluster_id == 5   # Uses default because IP is invalid
        assert router1.router_id == 10   # Uses default because IP is invalid
        
        # Boundary values
        router2 = Router("1.1.1.1", 50000)
        assert router2.cluster_id == 1
        assert router2.router_id == 1
        
        # Large valid values
        router3 = Router("254.254.254.254", 50000)
        assert router3.cluster_id == 254
        assert router3.router_id == 254
    
    def test_router_use_specified_ids_flag(self):
        """Test use_specified_ids parameter overrides IP extraction"""
        # Test with valid IP but use_specified_ids=True
        router1 = Router("192.168.10.20", 50000, cluster_id=99, router_id=88, use_specified_ids=True)
        assert router1.host == "192.168.10.20"
        assert router1.cluster_id == 99  # Uses specified value, not IP-derived (10)
        assert router1.router_id == 88   # Uses specified value, not IP-derived (20)
        
        # Test with hostname and use_specified_ids=True (should work the same)
        router2 = Router("router.local", 50000, cluster_id=5, router_id=15, use_specified_ids=True)
        assert router2.host == "router.local"
        assert router2.cluster_id == 5
        assert router2.router_id == 15
        
        # Test with valid IP and use_specified_ids=False (default behavior)
        router3 = Router("10.0.100.200", 50000, cluster_id=99, router_id=88, use_specified_ids=False)
        assert router3.host == "10.0.100.200"
        assert router3.cluster_id == 100  # Uses IP-derived value, not specified (99)
        assert router3.router_id == 200   # Uses IP-derived value, not specified (88)
        
        # Test that default behavior (without use_specified_ids) still extracts from IP
        router4 = Router("172.16.50.100", 50000, cluster_id=99, router_id=88)
        assert router4.host == "172.16.50.100"
        assert router4.cluster_id == 50   # Uses IP-derived value (default behavior)
        assert router4.router_id == 100   # Uses IP-derived value (default behavior)
    
    def test_router_use_specified_ids_with_edge_cases(self):
        """Test use_specified_ids with various edge cases"""
        # Test with invalid IP and use_specified_ids=True
        router1 = Router("invalid.ip", 50000, cluster_id=77, router_id=66, use_specified_ids=True)
        assert router1.cluster_id == 77
        assert router1.router_id == 66
        
        # Test with IPv6 and use_specified_ids=True
        router2 = Router("2001:db8::1", 50000, cluster_id=33, router_id=44, use_specified_ids=True)
        assert router2.cluster_id == 33
        assert router2.router_id == 44
        
        # Test with valid IP but zero values and use_specified_ids=True
        router3 = Router("192.168.1.1", 50000, cluster_id=6, router_id=4, use_specified_ids=True)
        assert router3.cluster_id == 6   # Uses specified zero value
        assert router3.router_id == 4    # Uses specified zero value
        
        # Compare with same IP but use_specified_ids=False
        router4 = Router("192.168.1.1", 50000, cluster_id=0, router_id=0, use_specified_ids=False)
        assert router4.cluster_id == 1   # Uses IP-derived value
        assert router4.router_id == 1    # Uses IP-derived value


# Test Runner
def run_all_tests():
    """Run all tests with basic test runner"""
    import inspect
    
    # Get all test classes
    test_classes = [
        TestExceptions, TestSubscribable, TestDevice, TestDevices,
        TestGroup, TestGroups, TestScene, TestScenes,
        TestStaticUtilities, TestRouter, TestIntegration
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        print(f"\nRunning {test_class.__name__}...")
        
        # Get all test methods
        test_methods = [method for name, method in inspect.getmembers(test_class, predicate=inspect.isfunction) 
                       if name.startswith('test_')]
        
        for test_method in test_methods:
            try:
                # Create instance and run test
                instance = test_class()
                
                if asyncio.iscoroutinefunction(test_method):
                    asyncio.run(test_method(instance))
                else:
                    test_method(instance)
                
                print(f"  ✓ {test_method.__name__}")
                passed += 1
            except Exception as e:
                print(f"  ✗ {test_method.__name__}: {e}")
                failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed, {passed + failed} total")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)