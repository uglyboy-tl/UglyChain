from __future__ import annotations

from dataclasses import dataclass
from importlib import resources

from playwright.sync_api import Page
from pydantic import BaseModel


class Coordinates(BaseModel):
    x: int
    y: int


class CoordinateSet(BaseModel):
    top_left: Coordinates
    top_right: Coordinates
    bottom_left: Coordinates
    bottom_right: Coordinates
    center: Coordinates
    width: int
    height: int


class ViewportInfo(BaseModel):
    scroll_x: int
    scroll_y: int
    width: int
    height: int


@dataclass(frozen=False)
class DOMBaseNode:
    is_visible: bool
    # Use None as default and set parent later to avoid circular reference issues
    parent: DOMElementNode | None


@dataclass(frozen=False)
class DOMTextNode(DOMBaseNode):
    text: str
    type: str = "TEXT_NODE"

    def has_parent_with_highlight_index(self) -> bool:
        current = self.parent
        while current is not None:
            if current.highlight_index is not None:
                return True
            current = current.parent
        return False


@dataclass(frozen=False)
class DOMElementNode(DOMBaseNode):
    """
    xpath: the xpath of the element from the last root node (shadow root or iframe OR document if no shadow root or iframe).
    To properly reference the element we need to recursively switch the root node until we find the element (work you way up the tree with `.parent`)
    """

    tag_name: str
    xpath: str
    attributes: dict[str, str]
    children: list[DOMBaseNode]
    is_interactive: bool = False
    is_top_element: bool = False
    shadow_root: bool = False
    highlight_index: int | None = None
    viewport_coordinates: CoordinateSet | None = None
    page_coordinates: CoordinateSet | None = None
    viewport_info: ViewportInfo | None = None

    def __repr__(self) -> str:
        tag_str = f"<{self.tag_name}"

        # Add attributes
        for key, value in self.attributes.items():
            tag_str += f' {key}="{value}"'
        tag_str += ">"

        # Add extra info
        extras = []
        if self.is_interactive:
            extras.append("interactive")
        if self.is_top_element:
            extras.append("top")
        if self.shadow_root:
            extras.append("shadow-root")
        if self.highlight_index is not None:
            extras.append(f"highlight:{self.highlight_index}")

        if extras:
            tag_str += f" [{', '.join(extras)}]"

        return tag_str

    def get_all_text_till_next_clickable_element(self, max_depth: int = -1) -> str:
        text_parts = []

        def collect_text(node: DOMBaseNode, current_depth: int) -> None:
            if max_depth != -1 and current_depth > max_depth:
                return

            # Skip this branch if we hit a highlighted element (except for the current node)
            if isinstance(node, DOMElementNode) and node != self and node.highlight_index is not None:
                return

            if isinstance(node, DOMTextNode):
                text_parts.append(node.text)
            elif isinstance(node, DOMElementNode):
                for child in node.children:
                    collect_text(child, current_depth + 1)

        collect_text(self, 0)
        return "\n".join(text_parts).strip()

    def clickable_elements_to_string(self, include_attributes: list[str] | None = None) -> str:
        """Convert the processed DOM content to HTML."""
        if include_attributes is None:
            include_attributes = []
        formatted_text = []

        def process_node(node: DOMBaseNode, depth: int) -> None:
            if isinstance(node, DOMElementNode):
                # Add element with highlight_index
                if node.highlight_index is not None:
                    attributes_str = ""
                    if include_attributes:
                        attributes_str = " " + " ".join(
                            f'{key}="{value}"' for key, value in node.attributes.items() if key in include_attributes
                        )
                    formatted_text.append(
                        f"[{node.highlight_index}]<{node.tag_name}{attributes_str}>{node.get_all_text_till_next_clickable_element()}</{node.tag_name}>"
                    )

                # Process children regardless
                for child in node.children:
                    process_node(child, depth + 1)

            elif isinstance(node, DOMTextNode):
                # Add text only if it doesn't have a highlighted parent
                if not node.has_parent_with_highlight_index():
                    formatted_text.append(f"[]{node.text}")

        process_node(self, 0)
        return "\n".join(formatted_text)


SelectorMap = dict[int, DOMElementNode]


@dataclass
class DOMState:
    element_tree: DOMElementNode
    selector_map: SelectorMap


class DomService:
    def __init__(self, page: Page):
        self.page = page

    # region - Clickable elements
    def get_clickable_elements(
        self,
        highlight_elements: bool = True,
        focus_element: int = -1,
        viewport_expansion: int = 0,
    ) -> DOMState:
        element_tree = self._build_dom_tree(highlight_elements, focus_element, viewport_expansion)
        selector_map = self._create_selector_map(element_tree)

        return DOMState(element_tree=element_tree, selector_map=selector_map)

    def _build_dom_tree(
        self,
        highlight_elements: bool,
        focus_element: int,
        viewport_expansion: int,
    ) -> DOMElementNode:
        js_code = resources.read_text("uglychain.tools.browser_use", "buildDomTree.js")

        args = {
            "doHighlightElements": highlight_elements,
            "focusHighlightIndex": focus_element,
            "viewportExpansion": viewport_expansion,
        }

        eval_page = self.page.evaluate(js_code, args)  # This is quite big, so be careful
        html_to_dict = self._parse_node(eval_page)

        if html_to_dict is None or not isinstance(html_to_dict, DOMElementNode):
            raise ValueError("Failed to parse HTML to dictionary")

        return html_to_dict

    def _create_selector_map(self, element_tree: DOMElementNode) -> SelectorMap:
        selector_map = {}

        def process_node(node: DOMBaseNode) -> None:
            if isinstance(node, DOMElementNode):
                if node.highlight_index is not None:
                    selector_map[node.highlight_index] = node

                for child in node.children:
                    process_node(child)

        process_node(element_tree)
        return selector_map

    def _parse_node(
        self,
        node_data: dict,
        parent: DOMElementNode | None = None,
    ) -> DOMBaseNode | None:
        if not node_data:
            return None

        if node_data.get("type") == "TEXT_NODE":
            text_node = DOMTextNode(
                text=node_data["text"],
                is_visible=node_data["isVisible"],
                parent=parent,
            )
            return text_node

        tag_name = node_data["tagName"]

        # Parse coordinates if they exist
        viewport_coordinates = None
        page_coordinates = None
        viewport_info = None

        if "viewportCoordinates" in node_data:
            viewport_coordinates = CoordinateSet(
                top_left=Coordinates(**node_data["viewportCoordinates"]["topLeft"]),
                top_right=Coordinates(**node_data["viewportCoordinates"]["topRight"]),
                bottom_left=Coordinates(**node_data["viewportCoordinates"]["bottomLeft"]),
                bottom_right=Coordinates(**node_data["viewportCoordinates"]["bottomRight"]),
                center=Coordinates(**node_data["viewportCoordinates"]["center"]),
                width=node_data["viewportCoordinates"]["width"],
                height=node_data["viewportCoordinates"]["height"],
            )

        if "pageCoordinates" in node_data:
            page_coordinates = CoordinateSet(
                top_left=Coordinates(**node_data["pageCoordinates"]["topLeft"]),
                top_right=Coordinates(**node_data["pageCoordinates"]["topRight"]),
                bottom_left=Coordinates(**node_data["pageCoordinates"]["bottomLeft"]),
                bottom_right=Coordinates(**node_data["pageCoordinates"]["bottomRight"]),
                center=Coordinates(**node_data["pageCoordinates"]["center"]),
                width=node_data["pageCoordinates"]["width"],
                height=node_data["pageCoordinates"]["height"],
            )

        if "viewport" in node_data:
            viewport_info = ViewportInfo(
                scroll_x=node_data["viewport"]["scrollX"],
                scroll_y=node_data["viewport"]["scrollY"],
                width=node_data["viewport"]["width"],
                height=node_data["viewport"]["height"],
            )

        element_node = DOMElementNode(
            tag_name=tag_name,
            xpath=node_data["xpath"],
            attributes=node_data.get("attributes", {}),
            children=[],  # Initialize empty, will fill later
            is_visible=node_data.get("isVisible", False),
            is_interactive=node_data.get("isInteractive", False),
            is_top_element=node_data.get("isTopElement", False),
            highlight_index=node_data.get("highlightIndex"),
            shadow_root=node_data.get("shadowRoot", False),
            parent=parent,
            viewport_coordinates=viewport_coordinates,
            page_coordinates=page_coordinates,
            viewport_info=viewport_info,
        )

        children: list[DOMBaseNode] = []
        for child in node_data.get("children", []):
            if child is not None:
                child_node = self._parse_node(child, parent=element_node)
                if child_node is not None:
                    children.append(child_node)

        element_node.children = children

        return element_node
