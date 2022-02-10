DEFAULT_FADE_TIME = 50  # ms


PROTOCOL = {
    1: "DALI",
    2: "DIGIDIM",
    3: "SDIM",
    4: "DMX",
}


UNKNOWN_PROTOCOL = "Unknown Protocol"


DALI_TYPES = {
    1: "Fluorescent Lamps",
    2: "Self contained emergency lighting",
    3: "Discharge lamps",
    4: "Low voltage halogen lamps",
    5: "Conversion to D.C.",
    6: "LED modules",
    7: "Switching function",
    8: "Colour control",
    9: "Sequencer",
}


UNKNOWN_DALI_TYPE = "Unknown DALI Device"


UNKNOWN_DIGIDIM_TYPE = "Unknown DIGIDIM Device"


def h_2_d(a, b, c):
    return (a << 16) + (b << 8) + c


class DigidimType:
    def __init__(self, part_number, name, is_load=True) -> None:
        self.part_number = part_number
        self.name = name
        self.is_load = is_load

    def __str__(self):
        return f"{self.part_number} - {self.name}"


class DeviceStateFlag:
    def __init__(self, state, description) -> None:
        self.state = state
        self.property = None
        self.description = description


# fmt: off

DIGIDIM_TYPES = {
    h_2_d(0x00, 0x10, 0x08): DigidimType("100", "Rotary", False),
    h_2_d(0x00, 0x11, 0x07): DigidimType("110", "Single Slider", False),
    h_2_d(0x00, 0x11, 0x14): DigidimType("111", "Double Slider", False),
    h_2_d(0x00, 0x12, 0x13): DigidimType("121", "2 Button on/off + IR", False),
    h_2_d(0x00, 0x12, 0x20): DigidimType("122", "2 Button modifier + IR", False),
    h_2_d(0x00, 0x12, 0x44): DigidimType("124", "5 Button + IR", False),
    h_2_d(0x00, 0x12, 0x51): DigidimType("125", "5 Button + modifier + IR", False),
    h_2_d(0x00, 0x12, 0x68): DigidimType("126", "8 Button + IR", False),
    h_2_d(0x00, 0x16, 0x57): DigidimType("165", "5 Button + modifier + IR", False),
    h_2_d(0x00, 0x16, 0x64): DigidimType("168", "8 Button + modifier + IR", False),
    h_2_d(0x00, 0x17, 0x01): DigidimType("170", "IR Receiver", False),
    h_2_d(0x00, 0x31, 0x25): DigidimType("312", "Multisensor", False),
    h_2_d(0x00, 0x41, 0x08): DigidimType("410", "Ballast Style 1-10V Converter", True),
    h_2_d(0x00, 0x41, 0x60): DigidimType("416S", "16A Dimmer", True),
    h_2_d(0x00, 0x42, 0x52): DigidimType("425S", "25A Dimmer", True),
    h_2_d(0x00, 0x44, 0x43): DigidimType("444", "Multi Input Unit", False),
    h_2_d(0x00, 0x45, 0x04): DigidimType("450", "800W Dimmer", True),
    h_2_d(0x00, 0x45, 0x28): DigidimType("452", "1000W Universal Dimmer", True),
    h_2_d(0x00, 0x45, 0x59): DigidimType("455", "500W Thyristor Dimmer", True),
    h_2_d(0x00, 0x45, 0x80): DigidimType("458/DIM8", "8 Channel Dimmer", True),
    h_2_d(0x74, 0x45, 0x81): DigidimType("458/CTR8", "8 Channel Ballast Controller", True),
    h_2_d(0x04, 0x45, 0x83): DigidimType("458/SW8", "8 Channel Relay Unit", True),
    h_2_d(0x00, 0x45, 0x86): DigidimType("458/OPT", "4 Channel Options Module", True),
    h_2_d(0x00, 0x46, 0x03): DigidimType("460", "DALI to SDIM Converter", True),
    h_2_d(0x00, 0x47, 0x26): DigidimType("472", "Din Rail 1-10V Converter", True),
    h_2_d(0x00, 0x47, 0x40): DigidimType("474", "4 Channel Ballast Controller - Output Unit", True),
    h_2_d(0x00, 0x47, 0x41): DigidimType("474", "4 Channel Ballast Controller - Relay Unit", True),
    h_2_d(0x00, 0x49, 0x00): DigidimType("490", "Blinds Unit", True),
    h_2_d(0x00, 0x49, 0x48): DigidimType("494", "Blinds Relay", True),
    h_2_d(0x00, 0x49, 0x86): DigidimType("498", "Relay Unit", True),
    h_2_d(0x00, 0x80, 0x45): DigidimType("804", "Digidim 4", False),
    h_2_d(0x00, 0x92, 0x40): DigidimType("924", "LCD TouchPanel", False),
    h_2_d(0x00, 0x93, 0x56): DigidimType("935", "Scene Commander (6 Buttons)", False),
    h_2_d(0x00, 0x93, 0x94): DigidimType("939", "Scene Commander (10 Buttons)", False),
    h_2_d(0x00, 0x94, 0x24): DigidimType("942", "Analogue Input Unit", False),
}


DEVICE_STATE_FLAGS = {
    0x00000001: DeviceStateFlag("NSDisabled", "Device or subdevice has been disabled, usually an IR subdevice or a DMX channel"),
    0x00000002: DeviceStateFlag("NSLampFailure", "Unspecified lamp problem"),
    0x00000004: DeviceStateFlag("NSMissing", "The device previously existed but is not currently present"),
    0x00000008: DeviceStateFlag("NSFaulty", "Ran out of addresses (DALI subnet) / unknown Digidim control device / DALI that keeps responding with multi-replies"),
    0x00000010: DeviceStateFlag("NSRefreshing", "DALI subnet, DALI load or Digidim control device is being discovered"),
    0x00000020: DeviceStateFlag("NSReserved_0x20", "Internal use only"),
    0x00000040: DeviceStateFlag("NSReserved_0x40", ""),
    0x00000080: DeviceStateFlag("NSReserved_0x80", "Internal use only"),
    0x00000100: DeviceStateFlag("NSEM_Resting", "The load is intentionally off whilst the control gear is being powered by the emergency supply"),
    0x00000200: DeviceStateFlag("NSEM_Reserved_0x200", ""),
    0x00000400: DeviceStateFlag("NSEM_InEmergency", "No mains power is being supplied"),
    0x00000800: DeviceStateFlag("NSEM_InProlong", "Mains has been restored but device is still using the emergency supply"),
    0x00001000: DeviceStateFlag("NSEM_FTInProgress", "The Functional Test is in progress (brief test where the control gear is being powered by the emergency supply)"),
    0x00002000: DeviceStateFlag("NSEM_DTInProgress", "The Duration Test is in progress. This test involves operating the control gear using the battery until the battery is completely discharged. The duration that the control gear was operational for is recorded, and then the battery recharges itself from the mains supply"),
    0x00004000: DeviceStateFlag("NSEM_Reserved_0x4000", ""),
    0x00008000: DeviceStateFlag("NSEM_Reserved_0x8000", ""),
    0x00010000: DeviceStateFlag("NSEM_DTPending", "The Duration Test has been requested but has not yet commenced. The test can be delayed if the battery is not fully charged"),
    0x00020000: DeviceStateFlag("NSEM_FTPending", "The Functional Test has been requested but has not yet commenced. The test can be delayed if there is not enough charge in the battery"),
    0x00040000: DeviceStateFlag("NSEM_BatteryFail", "Battery has failed"),
    0x00080000: DeviceStateFlag("NSReserved_0x80000", "Internal use only"),
    0x00100000: DeviceStateFlag("NSReserved_0x100000", "Internal use only"),
    0x00200000: DeviceStateFlag("NSEM_Inhibit", "Prevents an emergency fitting from going into emergency mode"),
    0x00400000: DeviceStateFlag("NSEM_FTRequested", "Emergency Function Test has been requested"),
    0x00800000: DeviceStateFlag("NSEM_DTRequested", "Emergency Duration Test has been requested"),
    0x01000000: DeviceStateFlag("NSEM_Unknown", "Initial state of an emergency fitting"),
    0x02000000: DeviceStateFlag("NSOverTemperature", "Load is over temperature/heating"),
    0x04000000: DeviceStateFlag("NSOverCurrent", "Too much current is being drawn by the load"),
    0x08000000: DeviceStateFlag("NSCommsError", "Communications error"),
    0x10000000: DeviceStateFlag("NSSevereError", "Indicates that a load is either over temperature or drawing too much current, or both"),
    0x20000000: DeviceStateFlag("NSBadReply", "Indicates that a reply to a query was malformed"),
    0x40000000: DeviceStateFlag("NSReserved_0x40000000", ""),
    0x80000000: DeviceStateFlag("NSDeviceMismatch", "The actual load type does not match An attempt to match corresponding items in an Upload Design and a Workgroup Design / Real Workgroup. the expected type"),
}
# fmt: on
