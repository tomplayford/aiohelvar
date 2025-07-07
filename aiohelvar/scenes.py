from .parser.address import SceneAddress
from .parser.command import Command, CommandType
import logging

_LOGGER = logging.getLogger(__name__)


class Scene:
    def __init__(self, scene_address: SceneAddress, levels=None, name=None):
        self.name = name
        self.levels = levels
        self.address = scene_address

    def __eq__(self, o: object) -> bool:
        return self.address == o.address

    def __hash__(self) -> int:
        return hash(self.address)

    def __str__(self) -> str:
        return f"{self.address}: {self.name}"


class Scenes:
    def __init__(self, router):
        self.router = router
        self.scenes = {}

    def register_scene(self, scene_address, scene):
        self.scenes[scene_address] = scene

    def update_scene_name(self, scene_address, name):
        self.scenes[scene_address].name = name

    def get_scene(self, scene_address):
        return self.scenes[scene_address]

    def get_scenes_for_group(self, group_id: int, only_named=True):

        _LOGGER.info(
            f"There are {len(self.scenes.values())} registered scenes. We are looking for scenes with group {group_id}."
        )

        named_scenes = [
            scene
            for scene in self.scenes.values()
            if scene.address.group == int(group_id) and scene.name is not None
        ]
        named_scenes.sort(key=lambda x: x.name, reverse=False)

        if only_named:
            return named_scenes

        unnamed_scenes = [
            scene
            for scene in self.scenes.values()
            if scene.address.group == int(group_id) and scene.name is None
        ]
        unnamed_scenes.sort(key=lambda x: str(x.address), reverse=False)

        return named_scenes + unnamed_scenes


async def get_scenes(router, groups):

    response = await router._send_command_task(Command(CommandType.QUERY_SCENE_NAMES))

    for group in groups.groups.values():
        for block in range(1, 9):
            for scene in range(1, 17):
                scene = Scene(SceneAddress(int(group.group_id), int(block), int(scene)))
                router.scenes.register_scene(scene.address, scene)

    parts = response.result.strip("@").split("@")

    for part in parts:
        sub_parts = part.split(":")

        try:
            if len(sub_parts) < 2:
                _LOGGER.warning(f"Invalid scene part format: {part}")
                continue
            scene_address = SceneAddress(*[int(a) for a in sub_parts[0].split(".")])
            router.scenes.update_scene_name(scene_address, sub_parts[1])
        except (KeyError, ValueError, IndexError) as e:
            _LOGGER.error(f"Error parsing scene address {part}: {e}")

    # [router.scenes.register_scene(scene.address, scene) for scene in scenes]

    # for group in groups:
    #     router.groups.register_group(group)
    #     asyncio.create_task(update_name(router, group.group_id))
    #     asyncio.create_task(update_group_devices(router, group.group_id))
