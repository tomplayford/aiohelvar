from aiohelvar.parser.command_parameter import CommandParameterType
from .devices import Devices, get_devices
from .groups import Groups, get_groups
from .scenes import Scenes, get_scenes
from .parser.parser import CommandParser
from .parser.command_type import (
    COMMAND_TYPES_DONT_LISTEN_FOR_RESPONSE,
    CommandType,
    MessageType,
)
from .parser.command import Command
from .exceptions import CommandResponseTimeout, ParserError
import asyncio
import datetime
import logging

_LOGGER = logging.getLogger(__name__)


COMMAND_TERMINATOR = b"#"

# Some commands take a long time to process, and if the router has a significant queue, we
# can be waiting some time. Setting this to a somewhat absurd 30 seconds.
COMMAND_RESPONSE_TIMEOUT = 30

KEEP_ALIVE_PERIOD = 120


class Router:
    """Control a Helvar Route."""

    def __init__(self, host, port, cluster_id=0, router_id=1):
        self.host = host
        self.port = port
        self.cluster_id = cluster_id
        self.router_id = router_id

        self.config = None

        self.groups = Groups(self)

        self.devices = Devices(self)

        self.lights = None
        self.scenes = Scenes(self)
        self.sensors = None

        self.commands_to_send = asyncio.Queue()

        self.commands_received = []
        self.command_received = asyncio.Condition()

        self.connected = False

        self.workgroup_name = None
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
        _LOGGER.debug("Connecting...")

        try:
            self._reader, self._writer = await asyncio.open_connection(
                self.host, self.port
            )
        except ConnectionError as e:
            _LOGGER.error(
                f"Connection error while connecting to router {self.host}:{self.port} - ",
                e,
            )
            raise
        self.connected = True
        self._stream_reader_task = asyncio.create_task(
            self._stream_reader(self._reader)
        )
        self._stream_writer_task = asyncio.create_task(
            self._stream_writer(self._reader, self._writer)
        )

        # Read the workgroup name:
        response = await self._send_command_task(
            Command(CommandType.QUERY_WORKGROUP_NAME)
        )
        self.workgroup_name = response.result

        # Kick off the keepalive task
        self._keep_alive_task = asyncio.create_task(self._keep_alive())

    async def reconnect(self):
        await self.disconnect()
        await self.connect()

    async def disconnect(self):
        _LOGGER.info("Disconnecting...")
        tasks = [
            self._stream_reader_task,
            self._stream_writer_task,
            self._keep_alive_task,
        ]

        for task in tasks:
            if task is not None:
                task.cancel()

        self._writer.close()
        await self._writer.wait_closed()
        self.connected = False
        _LOGGER.info("Disconnected.")

    async def _keep_alive(self):
        """Keep the TCP connection alive. This'll also clean up any stale command futures."""

        def _keep_alive_callback(task):

            if task.exception():
                _LOGGER.warn(
                    f"Keep alive encountered an exception: {task.exception()}."
                )
                if isinstance(task.exception(), CommandResponseTimeout):
                    # Timeout - reconnect.
                    _LOGGER.warn("Keepalive didn't - reconnecting...")
                    asyncio.create_task(self.reconnect())
                    return
                else:
                    raise (task.exception())
            _LOGGER.debug("Keepalive kept the router TCP connection alive.")

        while True:
            await asyncio.sleep(KEEP_ALIVE_PERIOD)
            keepalive = await self.send_command(Command(CommandType.QUERY_ROUTER_TIME))

            keepalive.add_done_callback(_keep_alive_callback)

    async def _stream_reader(self, reader):
        _LOGGER.info("Connected.")
        parser = CommandParser()

        while True:
            line = await reader.readuntil(COMMAND_TERMINATOR)
            if line is not None:

                _LOGGER.debug(f"Received line: {line}")

                lines = line.split(b"$")
                if len(lines) > 1:
                    _LOGGER.debug(f"Split line by '$' into {len(lines)} lines")

                for splitline in lines:
                    _LOGGER.debug(f"Parsing line: {splitline}")
                    try:
                        command = parser.parse_command(splitline)
                    except ParserError as e:
                        _LOGGER.error(f"Exception handling line from router: {e}")
                    except Exception as e:
                        raise e
                    else:
                        _LOGGER.info(f"Received command: {command}")

                        if command.command_type == CommandType.RECALL_SCENE:
                            asyncio.create_task(self.handle_scene_recall(command))
                            continue

                        await self.command_received.acquire()
                        self.commands_received.append(command)
                        self.command_received.notify_all()
                        self.command_received.release()

    async def _stream_writer(self, reader, writer):

        while True:
            command_string = await self.commands_to_send.get()
            _LOGGER.info(f"Sending command '{command_string}'...")
            writer.write(command_string)
            # Small buffer. It's possible to overload a router.
            await asyncio.sleep(0.01)
            await writer.drain()
            self.commands_to_send.task_done()

    async def wait_for_pending_replies(self):
        while True:
            if len(self.command_received._waiters) == 0:
                return
            await asyncio.sleep(0.1)

    async def initialize(self):

        # Attempt Connection
        if not self.connected:
            await self.connect()

        # Get Groups
        await self.get_groups()

        # Get Devices
        await self.get_devices()

        # Get Clusters
        # await self.get_clusters()

        # Get Scenes
        await self.get_scenes()

    async def get_groups(self):

        await get_groups(self)

    async def get_devices(self):

        await get_devices(self)

    async def get_scenes(self):

        await get_scenes(self, self.groups)

    # async def get_clusters(self):
    #     response = await self.send_command(Command(CommandType.QUERY_ROUTERS))

    #     await response

    #     print(response.result())

    async def _send_command_task(self, command: Command):

        start_time = datetime.datetime.now()

        await self.send_string(str(command))

        def check_for_command_response():
            """Task that is scheduled after every command is sent. It checks for incoming messages
            from the router, looking for its reply.
            We match all command parameters, but we can't guarantee that identical requests don't steal
            eachothers replies."""

            for r_command in self.commands_received:
                if r_command.type_parameters_address == command.type_parameters_address:
                    # this is probably our response.
                    # We can safely remove ourselves from list as we stop iterating.

                    if r_command.command_message_type == MessageType.ERROR:
                        _LOGGER.error(
                            f"Request command {command} triggered an error back from the router: {r_command}."
                        )

                    self.commands_received.remove(r_command)
                    return r_command
            return None

        if command.command_type in COMMAND_TYPES_DONT_LISTEN_FOR_RESPONSE:
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

    async def send_command(self, command: Command) -> asyncio.Task:
        """
        Send command, return a future that'll return when we get a response back.
        We don't have request identifiers, so we have to use basic FIFO and
        assume the router executes commands in the order it received them.
        """
        return asyncio.create_task(self._send_command_task(command))

    async def send_string(self, string: str):
        await self.commands_to_send.put(bytes(string, "utf-8"))

    async def handle_scene_recall(self, command: Command):

        scene_address = command.get_scene_address()
        fade_time = command.get_param_value(CommandParameterType.FADE_TIME)

        await self.groups.handle_scene_callback(scene_address, fade_time)
