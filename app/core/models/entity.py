from sqlalchemy import BIGINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import pandas as pd

from app.core.utils.serializable import Serializable


class View(DeclarativeBase, Serializable):
    """
    The parent class for all DB views.
    """

    __is_view__ = True

    def __repr__(self):
        s = f"table_name: {self.__tablename__}\n"
        for key in self.__dict__.keys():
            val = getattr(self, key)
            if val is not None and not str(val).startswith("<"):
                s += f"{key}: {val}\n"
        return s

    def equals(self, obj:"View") -> bool:
        if not obj:
            return False
        return self.to_dict() == obj.to_dict()

    def to_df(self) -> pd.DataFrame: ... # TODO - potentially implement a general method

class Entity(DeclarativeBase, Serializable):
    """
    The parent class for all DB tables.
    """

    def __repr__(self):
        s = f"table_name: {self.__tablename__}\n"
        for key in self.__dict__.keys():
            val = getattr(self, key)
            if val is not None and not str(val).startswith("<"):
                s += f"{key}: {val}\n"
        return s

    def equals(self, obj:"Entity") -> bool:
        if not obj:
            return False
        return self.to_dict() == obj.to_dict()

    def to_df(self) -> pd.DataFrame: ... # TODO - potentially implement a general method

class FindableEntity(DeclarativeBase, Serializable):
    """
    The parent class for all DB tables which implement a global ID
    """
    gid:Mapped[BIGINT] = mapped_column(
        BIGINT,
        primary_key=True,
        unique=True,
        nullable=False
    )

    def get_name(self) -> str:
        t = type(self)
        return f"{t.__module__}.{t.__qualname__}"

    def __repr__(self):
        s = f"table_name: {self.__tablename__}\n"
        for key in self.__dict__.keys():
            val = getattr(self, key)
            if val is not None and not str(val).startswith("<"):
                s += f"{key}: {val}\n"
        return s

    def equals(self, obj:"FindableEntity") -> bool:
        if not obj:
            return False
        return self.to_dict() == obj.to_dict()

    def to_df(self) -> pd.DataFrame: ... # TODO - potentially implement a general method