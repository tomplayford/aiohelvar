import asyncio


class Subscribable:
    """Make a class subscribable.

    Used for Devices and Groups

    """

    def __init__(self) -> None:
        self.subscriptions = []

    def add_subscriber(self, func):
        self.subscriptions.append(func)

    def remove_subscriber(self, func):
        if func in self.subscriptions:
            self.subscriptions.remove(func)

    async def update_subscribers(self):
        for sub in self.subscriptions:
            await asyncio.create_task(sub(self))
