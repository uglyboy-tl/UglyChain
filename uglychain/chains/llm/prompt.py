#!/usr/bin/env python3

import re
from dataclasses import dataclass


@dataclass
class Prompt:
    """A class representing a prompt.

    Attributes:
        template: The template string for the prompt.
    """

    template: str = ""

    def format(self, **kwargs):
        """Format the prompt with the given kwargs.

        Args:
            **kwargs: Keyword arguments to replace placeholders in the template.

        Returns:
            The formatted prompt string.
        """

        def replace(match):
            key = match.group(1)
            value = kwargs.get(key, match.group(0))
            if isinstance(value, list):
                return "".join(str(x) for x in value)
            else:
                return str(value)

        pattern = r"(?<!{){([^{}\n]+)}(?!})"
        result = re.sub(pattern, replace, self.template)
        return result

    @property
    def input_variables(self):
        """Get a list of input variables in the template.

        Returns:
            A list of input variables.
        """
        return re.findall(r"(?<!{){([^{}\n]+)}(?!})", self.template)
