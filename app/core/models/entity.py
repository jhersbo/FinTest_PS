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