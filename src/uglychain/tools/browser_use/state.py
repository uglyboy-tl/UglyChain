from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .dom import DOMState

include_attributes: list[str] = []


@dataclass
class TabInfo:
    page_id: int
    url: str
    title: str


@dataclass
class BrowserState(DOMState):
    url: str
    title: str
    tabs: list[TabInfo]
    screenshot: str | None = None
    pixels_above: int = 0
    pixels_below: int = 0
    browser_errors: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        elements_text = self.element_tree.clickable_elements_to_string(include_attributes=include_attributes)

        has_content_above = (self.pixels_above or 0) > 0
        has_content_below = (self.pixels_below or 0) > 0

        if elements_text != "":
            if has_content_above:
                elements_text = (
                    f"... {self.pixels_above} pixels above - scroll or extract content to see more ...\n{elements_text}"
                )
            else:
                elements_text = f"[Start of page]\n{elements_text}"
            if has_content_below:
                elements_text = (
                    f"{elements_text}\n... {self.pixels_below} pixels below - scroll or extract content to see more ..."
                )
            else:
                elements_text = f"{elements_text}\n[End of page]"
        else:
            elements_text = "empty page"

        time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        step_info_description = f"Current date and time: {time_str}"

        state_description = f"""
[Current state starts here]
You will see the following only once - if you need to remember it and you dont know it yet, write it down in the memory:
Current url: {self.url}
Available tabs:
{self.tabs}
Interactive elements from current page:
{elements_text}
{step_info_description}
	"""
        return state_description
