from pydantic import BaseModel


class DataUpload(BaseModel):
    """A wrapper for the data upload location returned upon successful upload"""

    location: str
