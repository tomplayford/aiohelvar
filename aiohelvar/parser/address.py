class HelvarAddress:
    """
    Represents a Helvar device address.

    Address format is @c.r.s.d
    c - cluster: 0-253
    r - router: 1-254
    s - subnet: 1-4
    d - device: 1-255

    TODO: validate the above.

    incomplete addresses are possible, but must include at least cluster and router

    @0.1

    cluster: 0
    router: 1

    """

    def __init__(self, cluster, router, subnet=None, device=None):
        self.cluster = cluster
        self.router = router
        self.subnet = subnet
        self.device = device

    def __str__(self, separator="."):
        base = f"@{self.cluster}{separator}{self.router}"
        if self.subnet:
            base = f"{base}{separator}{self.subnet}"
        if self.device:
            return f"{base}{separator}{self.device}"
        return base

    def bus_type(self):

        if self.subnet in (1, 2):
            return "DALI"
        if self.subnet == 3:
            return "S-DIM"
        if self.subnet == 4:
            return "DMX"
        return None

    def __eq__(self, other):

        for a in ("cluster", "router", "subnet", "device"):

            if getattr(self, a) is not None:
                if getattr(other, a) is None:
                    return False
                if getattr(self, a) != getattr(other, a):
                    return False
            elif getattr(other, a) is not None:
                return False

        return True

    def __hash__(self):
        return hash((self.cluster, self.router, self.subnet, self.device))

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
        # TODO validate group, block and scene values are in range

        self.group = int(group)
        self.block = int(block)
        self.scene = int(scene)

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
        return self.block * 16 + self.scene

    def to_int(self) -> int:
        return self.group * (8 * 16) + self.block * 16 + self.scene
