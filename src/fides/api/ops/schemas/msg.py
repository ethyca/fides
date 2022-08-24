from pydantic import BaseModel


class Msg(BaseModel):
    """A schema for message objects"""

    msg: str
