from uglychain.utils import config

from .errors import ParseError

if config.output_format == "yaml":
    from .yaml import Instructor
elif config.output_format == "json":
    from .json import Instructor
else:
    Instructor = None

__all__ = [
    "ParseError",
    "Instructor",
]
