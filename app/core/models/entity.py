from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BIGINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import pandas as pd

def __to_dict__(obj:object) -> dict[str, Any]:
    return {
        k: v for k,v in vars(obj).items() if not k.startswith(("_","<","s_id"))
    }

def _serialize(v:Any) -> Any:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v

def __to_json__(obj:object) -> dict[str, Any]:
    return {k: _serialize(v) for k, v in __to_dict__(obj).items()}

class View(DeclarativeBase):
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

    def to_dict(self) -> dict[str, Any]:
        return __to_dict__(self)

    def to_json(self) -> dict[str, Any]:
        return __to_json__(self)

    def to_df(self) -> pd.DataFrame: ... # TODO - potentially implement a general method

class Entity(DeclarativeBase):
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

    def to_dict(self) -> dict[str, Any]:
        return __to_dict__(self)

    def to_json(self) -> dict[str, Any]:
        return __to_json__(self)

    def to_df(self) -> pd.DataFrame: ... # TODO - potentially implement a general method

class FindableEntity(DeclarativeBase):
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
        return self.__name__

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

    def to_dict(self) -> dict[str, Any]:
        return __to_dict__(self)

    def to_json(self) -> dict[str, Any]:
        return __to_json__(self)

    def to_df(self) -> pd.DataFrame: ... # TODO - potentially implement a general method