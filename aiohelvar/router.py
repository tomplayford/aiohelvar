

things_to_send = []

# from .config import Config
# from .groups import Groups
# from .lights import Lights
# from .scenes import Scenes
# from .sensors import Sensors
# from .errors import raise_error


class Router:
    """Control a Helvar Route."""

    def __init__(self, host, port, router_id=None):
        self.host = host
        self.port = port
        self._router_id = router_id

        self.config = None
        self.groups = None
        self.lights = None
        self.scenes = None
        self.sensors = None

        # self.capabilities = None
        # self.rules = None
        # self.schedules = None

    @property
    def id(self):
        """Return the ID of the router."""
        if self.config is not None:
            return self.config.routerid

        return self._router_id

    async def initialize(self):
        pass
        # result = await self.request("get", "")

        # self.config = Config(result["config"], self.request)
        # self.groups = Groups(result["groups"], self.request)
        # self.lights = Lights(result["lights"], self.request)
        # if "scenes" in result:
        #     self.scenes = Scenes(result["scenes"], self.request)
        # if "sensors" in result:
        #     self.sensors = Sensors(result["sensors"], self.request)

    async def request(self, method, path, json=None, auth=True):
        """Make a request to the API."""
        url = "http://{}/api/".format(self.host)
        if auth:
            url += "{}/".format(self.username)
        url += path

        async with self.websession.request(method, url, json=json) as res:
            res.raise_for_status()
            data = await res.json()
            _raise_on_error(data)
            return data


def _raise_on_error(data):
    """Check response for error message."""
    if isinstance(data, list):
        data = data[0]

    if isinstance(data, dict) and "error" in data:
        pass
    # raise_error(data["error"])
