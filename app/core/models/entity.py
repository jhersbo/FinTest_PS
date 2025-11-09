from sqlalchemy import BIGINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import pandas as pd

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
        if type(self) != type(obj):
            return False
        for key in self.__dict__.keys():
            s_val = getattr(self, key)
            o_val = getattr(obj, key)

            if not s_val or not o_val or s_val != o_val:
                return False
            
        for key in obj.__dict__.keys():
            s_val = getattr(self, key)
            o_val = getattr(obj, key)

            if not s_val or not o_val or s_val != o_val:
                return False
            
        return True
    
    def to_df(self) -> pd.DataFrame: ... # TODO - potentially implement a general method

class FindableEntity(DeclarativeBase):
    """
    The child class for all DB tables which implement a global ID
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
        if type(self) != type(obj):
            return False
        for key in self.__dict__.keys():
            s_val = getattr(self, key)
            o_val = getattr(obj, key)

            if not s_val or not o_val or s_val != o_val:
                return False
            
        for key in obj.__dict__.keys():
            s_val = getattr(self, key)
            o_val = getattr(obj, key)

            if not s_val or not o_val or s_val != o_val:
                return False
            
        return True
    
    def to_df(self) -> pd.DataFrame: ... # TODO - potentially implement a general method