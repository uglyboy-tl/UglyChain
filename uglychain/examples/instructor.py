from enum import Enum, unique
from pydantic import BaseModel, Field


@unique
class Gender(Enum):
    FEMALE = "FEMALE"
    MALE = "MALE"


class UserDetail(BaseModel):
    name: str
    gender: Gender


class AUTHOR(BaseModel):
    name: str = Field(..., description="姓名")
    introduction: str = Field(..., description="简介")
