from enum import Enum, EnumMeta


class ExtendableEnumMeta(EnumMeta):
    def __init__(cls, name, bases, atrtrs):
        super().__init__(name, bases, atrtrs)
        if not hasattr(cls, "_member_names_"):
            return
        base_names = {name for base in bases for name in getattr(base, "_member_names_", [])}
        for name in cls._member_names_:
            if name in base_names:
                delattr(cls, name)


class ExtendableEnum(Enum, metaclass=ExtendableEnumMeta):
    pass
