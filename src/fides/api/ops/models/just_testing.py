from sqlalchemy import Column, String

from fides.api.ops.schemas.base_class import BaseSchema


class JustTest(BaseSchema):
    test_field = Column(String(250))
