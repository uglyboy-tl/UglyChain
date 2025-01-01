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


class Unit(Enum):
    FAHRENHEIT = "fahrenheit"
    CELSIUS = "celsius"


def get_current_weather(location: str, unit: Unit = Unit.FAHRENHEIT) -> str:
    """Get the current weather in a given location.

    Args:
        location (str): The city and state, e.g., San Francisco, CA
        unit (Unit): The unit to use, e.g., fahrenheit or celsius
    """
    return "晴天，25华氏度"


def search_baidu(query: str) -> str:
    """Search Baidu for the query.

    Args:
        query (str): The query to search.
    """
    return f"{query}出生于1642年"


def search_google(query: str) -> str:
    """Search Google for the query.

    Args:
        query (str): The query to search.
    """
    return f"{query}是一个后端工程师"


def search_bing(query: str) -> str:
    """Search Bing for the query.

    Args:
        query (str): The query to search.
    """
    return f"{query}是一个技术博主"
