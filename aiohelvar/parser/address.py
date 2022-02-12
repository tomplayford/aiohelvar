class HelvarAddress:
    """
    Represents a Helvar device address.

    Address format is @c.r.s.d
    c - block: 0-253
    r - router: 1-254
    s - subnet: 1-4
    d - device: 1-255

    TODO: validate the above.

    incomplete addresses are possible, but must include at least block and router

    @0.1

    block: 0
    router: 1

    """

    def __init__(self, block: int, router: int, subnet: int = None, device: int = None):

        self.subnet = subnet
        self.device = device
        self.block = block
        self.router = router

    def __str__(self, separator="."):
        base = f"@{self.block}{separator}{self.router}"
        if self.subnet:
            base = f"{base}{separator}{self.subnet}"
        if self.device:
            return f"{base}{separator}{self.device}"
        return base

    @property
    def block(self):
        return self.__block

    @block.setter
    def block(self, var):

        var = int(var)
        if 0 > var > 253:
            raise TypeError("Block must be between 1 and 4.")
        self.__block = var

    @property
    def router(self):
        return self.__router

    @router.setter
    def router(self, var):

        var = int(var)
        if 1 > var > 254:
            raise TypeError("Router must be between 1 and 4.")
        self.__router = var

    @property
    def subnet(self):
        return self.__subnet

    @subnet.setter
    def subnet(self, var):

        if var is not None:
            var = int(var)
            if 1 > var > 4:
                raise TypeError("Subnet must be between 1 and 4 or None.")
        self.__subnet = var

    @property
    def device(self):
        return self.__device

    @device.setter
    def device(self, var):

        if var is not None:
            var = int(var)
            if 1 > var > 255:
                raise TypeError("Device must be between 1 and 255 or None.")
        self.__device = var

    def bus_type(self):

        if self.subnet in (1, 2):
            return "DALI"
        if self.subnet == 3:
            return "S-DIM"
        if self.subnet == 4:
            return "DMX"
        return None

    def __eq__(self, other):

        for a in ("block", "router", "subnet", "device"):

            if getattr(self, a) is not None:
                if getattr(other, a) is None:
                    return False
                if getattr(self, a) != getattr(other, a):
                    return False
            elif getattr(other, a) is not None:
                return False

        return True

    def __hash__(self):
        return hash((int(self.block), int(self.router), int(self.subnet), self.device))

    def __ne__(self, other):
        return not (self == other)


class SceneAddress:
    """Represents a Helvar scene address.

    Address format is @g.b.c

    g - Group (0-128)
    b - Block (1-8)
    s - Scene (1-16)

    group 0 == Un-grouped

    """

    def __init__(self, group: int, block: int, scene: int):

        self.group = group
        self.block = block
        self.scene = scene

    @property
    def group(self):
        return self.__group

    @group.setter
    def group(self, var):

        var = int(var)
        if 0 > var > 128:
            raise TypeError("Group must be between 0 and 128.")
        self.__group = var

    @property
    def block(self):
        return self.__block

    @block.setter
    def block(self, var):

        var = int(var)
        if 1 > var > 8:
            raise TypeError("Block must be between 1 and 8.")
        self.__block = var

    @property
    def scene(self):
        return self.__scene

    @scene.setter
    def scene(self, var):

        var = int(var)
        if 1 > var > 16:
            raise TypeError("Scene must be between 1 and 6.")
        self.__scene = var

    def __str__(self):
        return f"@{self.group}.{self.block}.{self.scene}"

    def __hash__(self):
        return hash((self.group, self.block, self.scene))

    def __eq__(self, other):

        return (self.group, self.block, self.scene) == (
            other.group,
            other.block,
            other.scene,
        )

    def __ne__(self, other):
        return not (self == other)

    def to_device_int(self) -> int:
        return max(0, self.block - 1) * 16 + self.scene

    def to_int(self) -> int:
        return self.group * (8 * 16) + max(0, self.block - 1) * 16 + self.scene
