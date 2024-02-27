from enum import Enum, EnumMeta
from typing import TypeVar

T = TypeVar("T", bound=Enum)


def inheritable_enum(the_enum: T) -> T:
    if type(the_enum) is not EnumMeta:
        raise TypeError("Cannot add inheritable enum members to a non-enum object!")
    the_enum.__inheritable_members__ = []
    # noinspection PyProtectedMember
    for member in the_enum._member_names_:
        the_enum.__inheritable_members__.append(member)
    the_enum._member_names_ = []

    return the_enum
