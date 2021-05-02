
from .parser.command import Command, CommandParameter, CommandParameterType, CommandType


def build_scene_address(group, block, scene):
    return f"@{group}.{block}.{scene}"

class Scene:
    def __init__(self, group, block, scene, name=None):
        self.group = group
        self.block = block
        self.scene = scene
        self.name = name

    @property
    def address(self):
        return build_scene_address(self.group, self.block, self.scene)

    def __eq__(self, o: object) -> bool:
        return self.group == o.group & self.block == o.block & self.scene == o.scene

    def __hash__(self) -> int:
        return hash(self.group, self.block, self.scene)

    def __str__(self) -> str:
        return f"Scene: {self.address} {self.name}"

class Scenes:
    def __init__(self, router):
        self.router = router
        self.scenes = {}

    def register_scene(self, scene_address, scene):
        self.scenes[scene_address] = scene


async def get_scenes(router):

    response = await router._send_command_task(Command(CommandType.QUERY_SCENE_NAMES))

    # # We expect a comma separated list of group ids. 
    # async def update_name(router, group_id):
    #     response = await router._send_command_task(
    #         CommandParameter(
    #             CommandType.QUERY_GROUP_DESCRIPTION, 
    #             [CommandParameter(CommandParameterType.GROUP, group_id)]
    #         ))
    #     router.groups.update_group_name(group_id, response.result)

    # async def update_group_devices(router, group_id):
    #     response = await router._send_command_task(
    #         Command(
    #             CommandType.QUERY_GROUP, 
    #             [CommandParameter(CommandParameterType.GROUP, group_id)]
    #         ))

    #     members = [member.strip("@") for member in response.result.split(",")]

    #     addresses = [HelvarAddress(*member.split('.')) for member in members]

    #     router.groups.update_group_device_members(group_id, addresses)

    parts = response.result.strip("@").split("@")
    scenes = []

    for part in parts:
        sub_parts = part.split(":")
        scenes.append(Scene(*sub_parts[0].split("."), sub_parts[1]))

    [router.scenes.register_scene(scene.address, scene) for scene in scenes]

    # for group in groups:
    #     router.groups.register_group(group)
    #     asyncio.create_task(update_name(router, group.group_id))
    #     asyncio.create_task(update_group_devices(router, group.group_id))
