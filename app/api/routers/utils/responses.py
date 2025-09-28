from enum import Enum

# RESPONSE TYPES
class ResponseTypes(Enum):
    JSON = "JSON"
# END RESPONSE TYPES

class WrappedException(Exception):
    def __init__(self, msg:str, status_code:int=500, *args):
        super().__init__(*args)
        self.msg = msg
        self.status_code = status_code
