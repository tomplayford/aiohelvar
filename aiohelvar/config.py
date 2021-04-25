class Config:
    """Represent Helvar config.
    """

    async def __init__(self, router,):
        self.router = router
        await self.update()

    @property
    def name(self):
        """Name of the router."""
        return self.raw["name"]

    @property
    def swversion(self):
        """Software version of the router."""
        return self.raw["swversion"]

    @property
    def modelid(self):
        """Model ID of the router."""
        return self.raw["modelid"]

    @property
    def routerid(self):
        """ID of the router."""
        return self.raw["routerid"]

    @property
    def apiversion(self):
        """Supported API version of the router."""
        return self.raw["apiversion"]

    @property
    def mac(self):
        """Mac address of the router."""
        return self.raw["mac"]

    async def update(self):
        self.raw = await self._request("get", "config")