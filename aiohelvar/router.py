from asyncio import exceptions
from .parser.command_type import CommandType
from .parser.command import Command
from .exceptions import CommandResponseTimeout, ParserError
from .parser.parser import CommandParser
import asyncio
import datetime

COMMAND_TERMINATOR = b"#"

# Some commands take a long time to process, and if the router has a significant queue, we
# can be waiting some time. Setting this to a somewhat absurd 30 seconds.
COMMAND_RESPONSE_TIMEOUT = 30

KEEP_ALIVE_PERIOD = 10

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

        self.commands_to_send = []
        self.command_to_send = asyncio.Event()

        self.commands_received = []
        self.command_received = asyncio.Condition()

        # self.capabilities = None
        # self.rules = None
        # self.schedules = None

    @property
    def id(self):
        """Return the ID of the router."""
        if self.config is not None:
            return self.config.routerid

        return self._router_id

    async def connect(self):
        print("Connecting...")
        self._reader, self._writer = await asyncio.open_connection(self.host, self.port)

        self._stream_reader_task = asyncio.create_task(
            self._stream_reader(self._reader)
        )
        self._stream_writer_task = asyncio.create_task(
            self._stream_writer(self._reader, self._writer)
        )

        # Kick off the keepalive task
        self._keep_alive_task = asyncio.create_task(self._keep_alive())

    async def reconnect(self):
        await self.disconnect()
        await self.connect()

    async def disconnect(self):
        print("Disconnecting...")
        tasks = [
            self._stream_reader_task,
            self._stream_writer_task,
            self._keep_alive_task,
        ]

        for task in tasks:
            if task is not None:
                task.cancel("Disconnecting...")

        self._writer.close()
        await self._writer.wait_closed()
        print("Disconnected")

    async def _keep_alive(self):
        """Keep the TCP connection alive. This'll also clean up any stale command futures."""

        def _keep_alive_callback(task):

            if task.exception():
                print(f"Keep alive encountered an exception: {task.exception()}.")
                if isinstance(task.exception(), CommandResponseTimeout):
                    # Timeout - reconnect.
                    print("Keepalive didn't - reconnecting...")
                    asyncio.create_task(self.reconnect())
                    return
                else:
                    raise (task.exception())
            print("Keepalive kept the connection alive.")

        while True:
            await asyncio.sleep(KEEP_ALIVE_PERIOD)
            keepalive = await self.send_command(Command(CommandType.QUERY_ROUTER_TIME))

            keepalive.add_done_callback(_keep_alive_callback)

    async def _stream_reader(self, reader):
        print("Connected.")
        parser = CommandParser()

        while True:
            line = await reader.readuntil(COMMAND_TERMINATOR)
            if line is not None:

                print(f"We've received the following: {line}")
                try:
                    command = parser.parse_command(line)
                except ParserError as e:
                    print(e)
                else:
                    print(f"Found the following command: {command}")
                    await self.command_received.acquire()
                    self.commands_received.append(command)
                    self.command_received.notify_all()
                    self.command_received.release()
            await asyncio.sleep(0.1)

    async def _stream_writer(self, reader, writer):

        while True:
            await self.command_to_send.wait()
            if len(self.commands_to_send) > 0:
                thing = self.commands_to_send.pop()
                print(f"found {thing} to send. Sending...")
                writer.write(thing)
                await writer.drain()
                print("Sent!")
            else:
                self.command_to_send.clear()

    async def initialize(self):

        # Attempt Connection
        await self.connect()

        first_command = await self.send_command(Command(CommandType.QUERY_ROUTER_TIME))
        second_command = await self.send_command(Command(CommandType.QUERY_GROUPS))
        third_command = await self.send_command(Command(CommandType.QUERY_ROUTER_TIME))
        forth_command = await self.send_command(Command(CommandType.QUERY_GROUPS))

        first_command.add_done_callback(
            lambda one: print(f"1st command got reply: {one.result()}")
        )
        second_command.add_done_callback(
            lambda one: print(f"2nd command got reply {one.result()}")
        )
        third_command.add_done_callback(
            lambda one: print(f"3rd command got reply {one.result()}")
        )
        forth_command.add_done_callback(
            lambda one: print(f"4th command got reply {one.result()}")
        )

        # result = await self.request("get", "")

        # self.config = Config(result["config"], self.request)
        # self.groups = Groups(result["groups"], self.request)
        # self.lights = Lights(result["lights"], self.request)
        # if "scenes" in result:
        # if "sensors" in result:
        #     self.sensors = Sensors(result["sensors"], self.request)

    async def _send_command_task(self, command: Command):

        start_time = datetime.datetime.now()

        await self.send_string(str(command))

        def check_for_command_response():
            for r_command in self.commands_received:
                if r_command.command_type == command.command_type:
                    # this is probably our response.
                    # We can safely remove from list as we stop iterating.
                    self.commands_received.remove(r_command)
                    return r_command
            return None

        response = check_for_command_response()

        if response:
            return response

        async with self.command_received:
            while response is None:

                if datetime.datetime.now() > (
                    start_time + datetime.timedelta(0, COMMAND_RESPONSE_TIMEOUT)
                ):
                    raise CommandResponseTimeout(command)

                await self.command_received.wait()

                response = check_for_command_response()
                if response:
                    break

        return response

    async def send_command(self, command: Command):
        """
        Send command, return a future that'll return when we get a response back.
        We don't have request identifiers, so we have to use basic FIFO and
        assume the router executes commands in the order it received them.
        """
        return asyncio.create_task(self._send_command_task(command))

    async def send_string(self, string: str):
        self.commands_to_send.append(bytes(string, "utf-8"))
        self.command_to_send.set()
