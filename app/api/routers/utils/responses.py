from enum import Enum

from fastapi import status

# RESPONSE TYPES
class ResponseTypes(Enum):
    JSON = "JSON"
# END RESPONSE TYPES

class WrappedException(Exception):
    def __init__(self, msg:str, status_code:int=500, *args):
        super().__init__(*args)
        self.msg = msg
        self.status_code = status_code

class BadTokenException(WrappedException):
    def __init__(
            self,
            msg="Invalid or missing API token. Please verify or obtain a new one. ",
            status_code = status.HTTP_400_BAD_REQUEST,
            *args
        ):
        super().__init__(msg, status_code, *args)
