from sqlalchemy.orm import DeclarativeBase

class Entity(DeclarativeBase):
    """
    The parent class for all DB 'entities'.
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
