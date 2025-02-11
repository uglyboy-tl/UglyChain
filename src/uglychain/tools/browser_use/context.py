from __future__ import annotations

import base64
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from time import sleep, time
from typing import Any

from playwright.sync_api import BrowserContext as Context
from playwright.sync_api import ElementHandle, FrameLocator, Page

from .browser import Browser, BrowserError, URLNotAllowedError
from .dom import DOMElementNode, DomService, SelectorMap
from .state import BrowserState, TabInfo

logger = logging.getLogger(__name__)

allowed_domains: list[str] | None = None
include_dynamic_attributes: bool = True
viewport_expansion: int = 500
highlight_elements: bool = True
minimum_wait_page_load_time: float = 0.5
wait_for_network_idle_page_load_time: float = 1
maximum_wait_page_load_time: float = 5
save_downloads_path: str | None = None


@dataclass
class BrowserContext:
    _browser: Browser = field(init=False, default_factory=Browser)
    _page: Page = field(init=False)

    @property
    def context(self) -> Context:
        return self._browser.context

    @cached_property
    def current_page(self) -> Page:
        return self.context.new_page()

    @property
    def state(self) -> BrowserState:
        self._wait_for_page_and_frames_load()
        self.cached_state = self._update_state()
        return self.cached_state

    @cached_property
    def cached_state(self) -> BrowserState:
        """Get the initial state of the browser"""
        return BrowserState(
            element_tree=DOMElementNode(
                tag_name="root",
                is_visible=True,
                parent=None,
                xpath="",
                attributes={},
                children=[],
            ),
            selector_map={},
            url=self.current_page.url if self.current_page else "",
            title="",
            screenshot=None,
            tabs=[],
        )

    def navigate_to(self, url: str) -> None:
        self.current_page.goto(url)
        self.current_page.wait_for_load_state()

    def refresh_page(self) -> None:
        self.current_page.reload()
        self.current_page.wait_for_load_state()

    def go_back(self) -> None:
        try:
            # 10 ms timeout
            self.current_page.go_back(timeout=10, wait_until="domcontentloaded")
            # await self._wait_for_page_and_frames_load(timeout_overwrite=1.0)
        except Exception as e:
            # Continue even if its not fully loaded, because we wait later for the page to load
            logger.debug(f"During go_back: {e}")

    def go_forward(self) -> None:
        try:
            self.current_page.go_forward(timeout=10, wait_until="domcontentloaded")
        except Exception as e:
            logger.debug(f"During go_forward: {e}")

    def close_current_tab(self) -> None:
        self.current_page.close()

        # otherwise the browser will be closed

    def get_page_html(self) -> str:
        return self.current_page.content()

    def execute_javascript(self, script: str) -> Any:
        return self.current_page.evaluate(script)

    def get_tabs_info(self) -> list[TabInfo]:
        tabs_info = []
        for page_id, page in enumerate(self.context.pages):
            tab_info = TabInfo(page_id=page_id, url=page.url, title=page.title())
            tabs_info.append(tab_info)

        return tabs_info

    def switch_to_tab(self, page_id: int) -> None:
        pages = self.context.pages

        if page_id >= len(pages):
            raise ValueError(f"No tab found with page_id: {page_id}")

        self.current_page = pages[page_id]
        self.current_page.bring_to_front()
        self.current_page.wait_for_load_state()

    def create_new_tab(self, url: str | None = None) -> None:
        self.current_page = self.context.new_page()
        self.current_page.wait_for_load_state()
        if url:
            self.current_page.goto(url)
            self.current_page.wait_for_load_state()

    @property
    def selector_map(self) -> SelectorMap:
        return self.cached_state.selector_map

    def get_element_by_index(self, index: int) -> ElementHandle | None:
        element_handle = self.get_locate_element(self.selector_map[index])
        return element_handle

    def get_dom_element_by_index(self, index: int) -> DOMElementNode:
        return self.selector_map[index]

    def is_file_uploader(self, element_node: DOMElementNode, max_depth: int = 3, current_depth: int = 0) -> bool:
        """Check if element or its children are file uploaders"""
        if current_depth > max_depth:
            return False

        # Check current element
        is_uploader = False

        if not isinstance(element_node, DOMElementNode):
            return False

        # Check for file input attributes
        if element_node.tag_name == "input":
            is_uploader = (
                element_node.attributes.get("type") == "file" or element_node.attributes.get("accept") is not None
            )

        if is_uploader:
            return True

        # Recursively check children
        if element_node.children and current_depth < max_depth:
            for child in element_node.children:
                if isinstance(child, DOMElementNode):
                    if self.is_file_uploader(child, max_depth, current_depth + 1):
                        return True

        return False

    def get_locate_element(self, element: DOMElementNode) -> ElementHandle | None:
        current_frame = self.current_page

        # Start with the target element and collect all parents
        parents: list[DOMElementNode] = []
        current = element
        while current.parent is not None:
            parent = current.parent
            parents.append(parent)
            current = parent

        # Reverse the parents list to process from top to bottom
        parents.reverse()

        # Process all iframe parents in sequence
        iframes = [item for item in parents if item.tag_name == "iframe"]
        for parent in iframes:
            css_selector = self._enhanced_css_selector_for_element(
                parent, include_dynamic_attributes=include_dynamic_attributes
            )
            current_frame = current_frame.frame_locator(css_selector)

        css_selector = self._enhanced_css_selector_for_element(
            element, include_dynamic_attributes=include_dynamic_attributes
        )

        try:
            if isinstance(current_frame, FrameLocator):
                element_handle = current_frame.locator(css_selector).element_handle()
                return element_handle
            else:
                # Try to scroll into view if hidden
                element_handle = current_frame.query_selector(css_selector)
                if element_handle:
                    element_handle.scroll_into_view_if_needed()
                    return element_handle
                return None
        except Exception as e:
            logger.error(f"Failed to locate element: {str(e)}")
            return None

    def _input_text_element_node(self, element_node: DOMElementNode, text: str) -> None:
        try:
            # Highlight before typing
            if element_node.highlight_index is not None:
                self._update_state(focus_element=element_node.highlight_index)

            element_handle = self.get_locate_element(element_node)

            if element_handle is None:
                raise Exception(f"Element: {repr(element_node)} not found")

            element_handle.scroll_into_view_if_needed(timeout=2500)
            element_handle.fill("")
            element_handle.type(text)
            self.current_page.wait_for_load_state()

        except Exception as e:
            raise Exception(f"Failed to input text into element: {repr(element_node)}. Error: {str(e)}") from e

    def _click_element_node(self, element_node: DOMElementNode) -> str | None:
        """
        Optimized method to click an element using xpath.
        Returns:
            str | None: Path to downloaded file if a download occurred, None otherwise
        """
        page = self.current_page

        try:
            # Highlight before clicking
            if element_node.highlight_index is not None:
                self._update_state(focus_element=element_node.highlight_index)

            element_handle = self.get_locate_element(element_node)

            if element_handle is None:
                raise Exception(f"Element: {repr(element_node)} not found")

            def perform_click(click_func: Callable[[], None]) -> str | None:
                """Performs the actual click, handling both download
                and navigation scenarios."""
                if save_downloads_path:
                    try:
                        # Try short-timeout expect_download to detect a file download has been been triggered
                        with page.expect_download(timeout=5000) as download_info:
                            click_func()
                        download = download_info.value
                        # If the download succeeds, save to disk
                        download_path = Path(save_downloads_path) / download.suggested_filename
                        download.save_as(download_path)
                        logger.debug(f"Download triggered. Saved file to: {download_path}")
                        return str(download_path)
                    except TimeoutError:
                        # If no download is triggered, treat as normal click
                        logger.debug("No download triggered within timeout. Checking navigation...")
                        page.wait_for_load_state()
                        self._check_and_handle_navigation(page)
                        return None
                else:
                    # Standard click logic if no download is expected
                    click_func()
                    page.wait_for_load_state()
                    self._check_and_handle_navigation(page)
                    return None

            try:
                return perform_click(lambda: element_handle.click(timeout=1500))
            except URLNotAllowedError as e:
                raise e
            except Exception:
                try:
                    return perform_click(lambda: page.evaluate("(el) => el.click()", element_handle))
                except URLNotAllowedError as e:
                    raise e
                except Exception as e:
                    raise Exception(f"Failed to click element: {str(e)}") from e

        except URLNotAllowedError as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to click element: {repr(element_node)}. Error: {str(e)}") from e

    def _check_and_handle_navigation(self, page: Page) -> None:
        """Check if current page URL is allowed and handle if not."""
        if not self._is_url_allowed(page.url):
            logger.warning(f"Navigation to non-allowed URL detected: {page.url}")
            try:
                self.go_back()
            except Exception as e:
                logger.error(f"Failed to go back after detecting non-allowed URL: {str(e)}")
            raise URLNotAllowedError(f"Navigation to non-allowed URL: {page.url}")

    def _is_url_allowed(self, url: str) -> bool:
        """Check if a URL is allowed based on the whitelist configuration."""
        if not allowed_domains:
            return True

        try:
            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()

            # Remove port number if present
            if ":" in domain:
                domain = domain.split(":")[0]

            # Check if domain matches any allowed domain pattern
            return any(
                domain == allowed_domain.lower() or domain.endswith("." + allowed_domain.lower())
                for allowed_domain in allowed_domains
            )
        except Exception as e:
            logger.error(f"Error checking URL allowlist: {str(e)}")
            return False

    def _update_state(self, focus_element: int = -1) -> BrowserState:
        # Check if current page is still valid, if not switch to another available page
        try:
            page = self.current_page
            # Test if page is still accessible
            page.evaluate("1")
        except Exception as e:
            logger.debug(f"Current page is no longer accessible: {str(e)}")
            # Get all available pages
            pages = self.context.pages
            if pages:
                self._page = pages[-1]
                page = self.current_page
                logger.debug(f"Switched to page: {page.title()}")
            else:
                raise BrowserError("Browser closed: no valid pages available") from e

        try:
            self.remove_highlights()
            dom_service = DomService(page)
            content = dom_service.get_clickable_elements(
                focus_element=focus_element,
                viewport_expansion=viewport_expansion,
                highlight_elements=highlight_elements,
            )

            screenshot_b64 = self.take_screenshot()
            pixels_above, pixels_below = self.get_scroll_info(page)

            self.current_state = BrowserState(
                element_tree=content.element_tree,
                selector_map=content.selector_map,
                url=page.url,
                title=page.title(),
                tabs=self.get_tabs_info(),
                screenshot=screenshot_b64,
                pixels_above=pixels_above,
                pixels_below=pixels_below,
            )

            return self.current_state
        except Exception as e:
            logger.error(f"Failed to update state: {str(e)}")
            # Return last known good state if available
            if hasattr(self, "current_state"):
                return self.current_state
            raise

    def remove_highlights(self) -> None:
        """
        Removes all highlight overlays and labels created by the highlightElement function.
        Handles cases where the page might be closed or inaccessible.
        """
        try:
            self.current_page.evaluate(
                """
                try {
                    // Remove the highlight container and all its contents
                    const container = document.getElementById('playwright-highlight-container');
                    if (container) {
                        container.remove();
                    }

                    // Remove highlight attributes from elements
                    const highlightedElements = document.querySelectorAll('[browser-user-highlight-id^="playwright-highlight-"]');
                    highlightedElements.forEach(el => {
                        el.removeAttribute('browser-user-highlight-id');
                    });
                } catch (e) {
                    console.error('Failed to remove highlights:', e);
                }
                """
            )
        except Exception as e:
            logger.debug(f"Failed to remove highlights (this is usually ok): {str(e)}")
            # Don't raise the error since this is not critical functionality
            pass

    def take_screenshot(self, full_page: bool = False) -> str:
        screenshot = self.current_page.screenshot(
            full_page=full_page,
            animations="disabled",
        )

        screenshot_b64 = base64.b64encode(screenshot).decode("utf-8")

        # await self.remove_highlights()

        return screenshot_b64

    def get_scroll_info(self, page: Page) -> tuple[int, int]:
        """Get scroll position information for the current page."""
        scroll_y = page.evaluate("window.scrollY")
        viewport_height = page.evaluate("window.innerHeight")
        total_height = page.evaluate("document.documentElement.scrollHeight")
        pixels_above = scroll_y
        pixels_below = total_height - (scroll_y + viewport_height)
        return pixels_above, pixels_below

    @classmethod
    def _convert_simple_xpath_to_css_selector(cls, xpath: str) -> str:
        """Converts simple XPath expressions to CSS selectors."""
        if not xpath:
            return ""

        # Remove leading slash if present
        xpath = xpath.lstrip("/")

        # Split into parts
        parts = xpath.split("/")
        css_parts = []

        for part in parts:
            if not part:
                continue

            # Handle index notation [n]
            if "[" in part:
                base_part = part[: part.find("[")]
                index_part = part[part.find("[") :]

                # Handle multiple indices
                indices = [i.strip("[]") for i in index_part.split("]")[:-1]]

                for idx in indices:
                    try:
                        # Handle numeric indices
                        if idx.isdigit():
                            index = int(idx) - 1
                            base_part += f":nth-of-type({index + 1})"
                        # Handle last() function
                        elif idx == "last()":
                            base_part += ":last-of-type"
                        # Handle position() functions
                        elif "position()" in idx:
                            if ">1" in idx:
                                base_part += ":nth-of-type(n+2)"
                    except ValueError:
                        continue

                css_parts.append(base_part)
            else:
                css_parts.append(part)

        base_selector = " > ".join(css_parts)
        return base_selector

    @classmethod
    def _enhanced_css_selector_for_element(
        cls, element: DOMElementNode, include_dynamic_attributes: bool = True
    ) -> str:
        """
        Creates a CSS selector for a DOM element, handling various edge cases and special characters.

        Args:
                element: The DOM element to create a selector for

        Returns:
                A valid CSS selector string
        """
        try:
            # Get base selector from XPath
            css_selector = cls._convert_simple_xpath_to_css_selector(element.xpath)

            # Handle class attributes
            if "class" in element.attributes and element.attributes["class"] and include_dynamic_attributes:
                # Define a regex pattern for valid class names in CSS
                valid_class_name_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")

                # Iterate through the class attribute values
                classes = element.attributes["class"].split()
                for class_name in classes:
                    # Skip empty class names
                    if not class_name.strip():
                        continue

                    # Check if the class name is valid
                    if valid_class_name_pattern.match(class_name):
                        # Append the valid class name to the CSS selector
                        css_selector += f".{class_name}"
                    else:
                        # Skip invalid class names
                        continue

            # Expanded set of safe attributes that are stable and useful for selection
            SAFE_ATTRIBUTES = {  # noqa: N806
                # Data attributes (if they're stable in your application)
                "id",
                # Standard HTML attributes
                "name",
                "type",
                "placeholder",
                # Accessibility attributes
                "aria-label",
                "aria-labelledby",
                "aria-describedby",
                "role",
                # Common form attributes
                "for",
                "autocomplete",
                "required",
                "readonly",
                # Media attributes
                "alt",
                "title",
                "src",
                # Custom stable attributes (add any application-specific ones)
                "href",
                "target",
            }

            if include_dynamic_attributes:
                dynamic_attributes = {
                    "data-id",
                    "data-qa",
                    "data-cy",
                    "data-testid",
                }
                SAFE_ATTRIBUTES.update(dynamic_attributes)

            # Handle other attributes
            for attribute, value in element.attributes.items():
                if attribute == "class":
                    continue

                # Skip invalid attribute names
                if not attribute.strip():
                    continue

                if attribute not in SAFE_ATTRIBUTES:
                    continue

                # Escape special characters in attribute names
                safe_attribute = attribute.replace(":", r"\:")

                # Handle different value cases
                if value == "":
                    css_selector += f"[{safe_attribute}]"
                elif any(char in value for char in "\"'<>`\n\r\t"):
                    # Use contains for values with special characters
                    # Regex-substitute *any* whitespace with a single space, then strip.
                    collapsed_value = re.sub(r"\s+", " ", value).strip()
                    # Escape embedded double-quotes.
                    safe_value = collapsed_value.replace('"', '\\"')
                    css_selector += f'[{safe_attribute}*="{safe_value}"]'
                else:
                    css_selector += f'[{safe_attribute}="{value}"]'

            return css_selector

        except Exception:
            # Fallback to a more basic selector if something goes wrong
            tag_name = element.tag_name or "*"
            return f"{tag_name}[highlight_index='{element.highlight_index}']"

    def _wait_for_page_and_frames_load(self, timeout_overwrite: float | None = None) -> None:
        """
        Ensures page is fully loaded before continuing.
        Waits for either network to be idle or minimum WAIT_TIME, whichever is longer.
        Also checks if the loaded URL is allowed.
        """
        # Start timing
        start_time = time()

        # Wait for page load
        try:
            self._wait_for_stable_network()

            # Check if the loaded URL is allowed
            self._check_and_handle_navigation(self.current_page)
        except URLNotAllowedError as e:
            raise e
        except Exception:
            logger.warning("Page load failed, continuing...")
            pass

        # Calculate remaining time to meet minimum WAIT_TIME
        elapsed = time() - start_time
        remaining = max((timeout_overwrite or minimum_wait_page_load_time) - elapsed, 0)

        logger.debug(f"--Page loaded in {elapsed:.2f} seconds, waiting for additional {remaining:.2f} seconds")

        # Sleep remaining time if needed
        if remaining > 0:
            sleep(remaining)

    def _wait_for_stable_network(self) -> None:
        page = self.current_page

        pending_requests = set()
        last_activity = time()

        # Define relevant resource types and content types
        RELEVANT_RESOURCE_TYPES = {  # noqa: N806
            "document",
            "stylesheet",
            "image",
            "font",
            "script",
            "iframe",
        }

        RELEVANT_CONTENT_TYPES = {  # noqa: N806
            "text/html",
            "text/css",
            "application/javascript",
            "image/",
            "font/",
            "application/json",
        }

        # Additional patterns to filter out
        IGNORED_URL_PATTERNS = {  # noqa: N806
            # Analytics and tracking
            "analytics",
            "tracking",
            "telemetry",
            "beacon",
            "metrics",
            # Ad-related
            "doubleclick",  # codespell:ignore doubleclick
            "adsystem",
            "adserver",
            "advertising",
            # Social media widgets
            "facebook.com/plugins",
            "platform.twitter",
            "linkedin.com/embed",
            # Live chat and support
            "livechat",
            "zendesk",
            "intercom",
            "crisp.chat",
            "hotjar",
            # Push notifications
            "push-notifications",
            "onesignal",
            "pushwoosh",
            # Background sync/heartbeat
            "heartbeat",
            "ping",
            "alive",
            # WebRTC and streaming
            "webrtc",
            "rtmp://",
            "wss://",
            # Common CDNs for dynamic content
            "cloudfront.net",
            "fastly.net",
        }

        def on_request(request: Any) -> None:
            # Filter by resource type
            if request.resource_type not in RELEVANT_RESOURCE_TYPES:
                return

            # Filter out streaming, websocket, and other real-time requests
            if request.resource_type in {
                "websocket",
                "media",
                "eventsource",
                "manifest",
                "other",
            }:
                return

            # Filter out by URL patterns
            url = request.url.lower()
            if any(pattern in url for pattern in IGNORED_URL_PATTERNS):
                return

            # Filter out data URLs and blob URLs
            if url.startswith(("data:", "blob:")):
                return

            # Filter out requests with certain headers
            headers = request.headers
            if headers.get("purpose") == "prefetch" or headers.get("sec-fetch-dest") in [
                "video",
                "audio",
            ]:
                return

            nonlocal last_activity
            pending_requests.add(request)
            last_activity = time()
            # logger.debug(f'Request started: {request.url} ({request.resource_type})')

        def on_response(response: Any) -> None:
            request = response.request
            if request not in pending_requests:
                return

            # Filter by content type if available
            content_type = response.headers.get("content-type", "").lower()

            # Skip if content type indicates streaming or real-time data
            if any(
                t in content_type
                for t in [
                    "streaming",
                    "video",
                    "audio",
                    "webm",
                    "mp4",
                    "event-stream",
                    "websocket",
                    "protobuf",
                ]
            ):
                pending_requests.remove(request)
                return

            # Only process relevant content types
            if not any(ct in content_type for ct in RELEVANT_CONTENT_TYPES):
                pending_requests.remove(request)
                return

            # Skip if response is too large (likely not essential for page load)
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > 5 * 1024 * 1024:  # 5MB
                pending_requests.remove(request)
                return

            nonlocal last_activity
            pending_requests.remove(request)
            last_activity = time()
            # logger.debug(f'Request resolved: {request.url} ({content_type})')

        # Attach event listeners
        page.on("request", on_request)
        page.on("response", on_response)

        try:
            # Wait for idle time
            start_time = time()
            while True:
                sleep(0.1)
                now = time()
                if len(pending_requests) == 0 and (now - last_activity) >= wait_for_network_idle_page_load_time:
                    break
                if now - start_time > maximum_wait_page_load_time:
                    logger.debug(
                        f"Network timeout after {maximum_wait_page_load_time}s with {len(pending_requests)} "
                        f"pending requests: {[r.url for r in pending_requests]}"
                    )
                    break

        finally:
            # Clean up event listeners
            page.remove_listener("request", on_request)
            page.remove_listener("response", on_response)

        logger.debug(f"Network stabilized for {wait_for_network_idle_page_load_time} seconds")
