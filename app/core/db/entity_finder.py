import importlib

from sqlalchemy.orm import DeclarativeBase

from app.core.db.session import current_session, transaction

from ..models.entity import FindableEntity
from ..models.globalid import GlobalId

# Chunk size for batch operations
BATCH_CHUNK_SIZE = 1000

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

    @staticmethod
    async def batch_create(objects:list[DeclarativeBase]) -> int:
        created = 0
        async with transaction() as _session:
            payload = []
            for i, obj in enumerate(objects):
                if isinstance(obj, FindableEntity):
                    gid = await GlobalId.allocate(obj)
                    obj.gid = gid.gid
                created += 1
                payload.append(obj)
                if i % BATCH_CHUNK_SIZE == 0 or i == len(objects) - 1:
                    _session.add_all(payload)
                    await _session.flush()
                    payload = []
        return created

    @staticmethod
    async def batch_update(objects:list[DeclarativeBase]) -> None:
        async with transaction() as _session:
            payload = []
            for i, obj in enumerate(objects):
                payload.append(obj)
                if i % BATCH_CHUNK_SIZE == 0 or i == len(objects) - 1:
                    _session.add_all(payload)
                    await _session.flush()
                    payload = []