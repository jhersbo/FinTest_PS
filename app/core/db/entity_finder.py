import importlib

from ..models.entity import FindableEntity
from ..models.globalid import GlobalId

class EntityFinder:

    @staticmethod
    async def find_by_gid(gid:int) -> FindableEntity:
        g_id = await GlobalId.find_by_gid(gid)
        classname = g_id.class_name
        finder = EntityFinder.resolve(f"{classname}.find_by_gid")
        return await finder(gid)

    @staticmethod
    def resolve(path: str):
        """
        Utility method to find a module based on a string path
        """

        parts = path.split('.')
        module_path = parts[0]
        try:
            module = importlib.import_module(module_path)
        except ImportError:
            for i in range(1, len(parts)):
                try:
                    module = importlib.import_module('.'.join(parts[:i+1]))
                except ImportError:
                    break
        obj = module
        for part in parts[len(module.__name__.split('.')):]:
            obj = getattr(obj, part)
        return obj