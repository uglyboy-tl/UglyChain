from __future__ import annotations

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


class Label(Enum):
    COUNTRY = "国家"
    CITY = "城市"
    MOVIE = "电影"
    TV = "电视剧"
    PERSON = "人物"


class ClassifyResponse(BaseModel):
    reason: str = Field(..., description="The reason to explain the classification.")
    label: Label = Field(..., description="The label of the classification.")
