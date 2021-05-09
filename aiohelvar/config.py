class Config:
    """Represent Helvar config."""

    async def __init__(
        self,
        router,
    ):
        self.router = router
        await self.update()

    @property
    def name(self):
        """Name of the router."""
        return self.raw["name"]

    async def update(self):
        self.raw = await self._request("get", "config")
