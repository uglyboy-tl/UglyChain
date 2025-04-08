from __future__ import annotations

import json
from collections.abc import Callable
from functools import wraps
from time import sleep
from typing import Any

from uglychain import Tool, llm

from .context import BrowserContext


@llm
def chat(prompt: str) -> str:
    return f"{prompt}"


def add_context(func: Callable[..., str]) -> Callable[..., str | tuple[str, str]]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> str | tuple[str, str]:
        action_result = func(*args, **kwargs)
        state = BrowserUse.browser.state
        result = f"""
[Action Result]
{action_result}
{state}
"""
        if state.screenshot:
            return result, state.screenshot
            # result += f"\u0001image:{state.screenshot}"  # 如果有截图，添加到结果中
        return result

    return wrapper


@Tool.tool
class BrowserUse:
    browser: BrowserContext = BrowserContext()

    @staticmethod
    @add_context
    def search_bing(query: str) -> str:
        "Search the query in Bing in the current tab, the query should be a search query like humans search in Bing, concrete and not vague or super long. More the single most important items."
        BrowserUse.browser.navigate_to(f"https://cn.bing.com/search?q={query}&form=QBLH&adlt=strict")
        msg = f'🔍  Searched for "{query}" in Bing'
        return msg

    @staticmethod
    @add_context
    def go_to_url(url: str) -> str:
        "Navigate to URL in the current tab in the browser"
        BrowserUse.browser.navigate_to(url)
        msg = f"🔗  Navigated to {url}"
        return msg

    @staticmethod
    @add_context
    def go_back() -> str:
        "Go back"
        BrowserUse.browser.go_back()
        msg = "🔙  Navigated back"
        return msg

    @staticmethod
    @add_context
    def click_element(index: int) -> str:
        "Click element in the browser"
        index = int(index)
        state = BrowserUse.browser.cached_state

        if index not in state.selector_map:
            raise Exception(f"Element with index {index} does not exist - retry or use alternative actions")

        element_node = state.selector_map[index]

        # if element has file uploader then dont click
        if BrowserUse.browser.is_file_uploader(element_node):
            msg = f"Index {index} - has an element which opens file upload dialog. To upload files please use a specific function to upload files "
            return msg

        msg = ""

        try:
            try:
                with BrowserUse.browser.context.expect_page(timeout=2000):
                    download_path = BrowserUse.browser._click_element_node(element_node)
                new_tab_msg = "New tab opened - switching to it"
            except TimeoutError:
                download_path = ""
                new_tab_msg = ""

            if download_path:
                msg = f"💾  Downloaded file to {download_path}"
            else:
                msg = f"🖱️  Clicked button with index {index}: {element_node.get_all_text_till_next_clickable_element(max_depth=2)}"

            if new_tab_msg:
                msg += f" - {new_tab_msg}"
                BrowserUse.browser.switch_to_tab(-1)
            return msg
        except Exception as e:
            return str(e)

    @staticmethod
    @add_context
    def input_text(index: int, text: str) -> str:
        "Input text into a input interactive element"
        index = int(index)
        state = BrowserUse.browser.cached_state

        if index not in state.selector_map:
            raise Exception(f"Element index {index} does not exist - retry or use alternative actions")

        element_node = state.selector_map[index]
        BrowserUse.browser._input_text_element_node(element_node, text)
        msg = f"⌨️  Input {text} into index {index}"
        return msg

    @staticmethod
    @add_context
    def switch_tab(page_id: int) -> str:
        "Switch tab"
        page_id = int(page_id)
        BrowserUse.browser.switch_to_tab(page_id)
        msg = f"🔄  Switched to tab {page_id}"
        return msg

    @staticmethod
    @add_context
    def open_tab(url: str) -> str:
        "Open url in new tab in the browser"
        BrowserUse.browser.create_new_tab(url)
        msg = f"🔗  Opened new tab with {url}"
        return msg

    @staticmethod
    @add_context
    def extract_content(goal: str) -> str:
        "Extract page content to retrieve specific information from the page, e.g. all company names, a specific description, all information about, links with companies in structured format or simply links"
        import markdownify  # type: ignore

        content = markdownify.markdownify(BrowserUse.browser.current_page.content())

        try:
            output = chat(
                f"Your task is to extract the content of the page. You will be given a page and a goal and you should extract all relevant information around this goal from the page. If the goal is vague, summarize the page. Respond in json format. Extraction goal: {goal}, Page: {content}"
            )
            msg = f"📄  Extracted from page\n: {output}\n"
            return msg
        except Exception:
            msg = f"📄  Extracted from page\n: {content}\n"
            return msg

    @staticmethod
    @add_context
    def scroll_down(amount: int = 0) -> str:
        "Scroll down the page by pixel amount - if no amount is specified, scroll down one page"
        amount = int(amount)
        if amount:
            BrowserUse.browser.current_page.evaluate(f"window.scrollBy(0, {amount});")
        else:
            BrowserUse.browser.current_page.evaluate("window.scrollBy(0, window.innerHeight);")

        amount_str = f"{amount} pixels" if amount > 0 else "one page"
        msg = f"🔍  Scrolled down the page by {amount_str}"
        return msg

    @staticmethod
    @add_context
    def scroll_up(amount: int = 0) -> str:
        "Scroll up the page by pixel amount - if no amount is specified, scroll up one page"
        amount = int(amount)
        if amount:
            BrowserUse.browser.current_page.evaluate(f"window.scrollBy(0, -{amount});")
        else:
            BrowserUse.browser.current_page.evaluate("window.scrollBy(0, -window.innerHeight);")

        amount_str = f"{amount} pixels" if amount > 0 else "one page"
        msg = f"🔍  Scrolled up the page by {amount_str}"
        return msg

    @staticmethod
    @add_context
    def send_keys(keys: str) -> str:
        "Send strings of special keys like Backspace, Insert, PageDown, Delete, Enter, Shortcuts such as `Control+o`, `Control+Shift+T` are supported as well. This gets used in keyboard.press. Be aware of different operating systems and their shortcuts"

        BrowserUse.browser.current_page.keyboard.press(keys)
        msg = f"⌨️  Sent keys: {keys}"
        return msg

    @staticmethod
    @add_context
    def scroll_to_text(text: str) -> str:
        "If you dont find something which you want to interact with, scroll to it"

        try:
            # Try different locator strategies
            locators = [
                BrowserUse.browser.current_page.get_by_text(text, exact=False),
                BrowserUse.browser.current_page.locator(f"text={text}"),
                BrowserUse.browser.current_page.locator(f"//*[contains(text(), '{text}')]"),
            ]

            for locator in locators:
                try:
                    # First check if element exists and is visible
                    if locator.count() > 0 and locator.first.is_visible():
                        locator.first.scroll_into_view_if_needed()
                        sleep(0.5)  # Wait for scroll to complete
                        msg = f"🔍  Scrolled to text: {text}"
                        return msg
                except Exception:
                    continue

            msg = f"Text '{text}' not found or not visible on page"
            return msg

        except Exception as e:
            msg = f"Failed to scroll to text '{text}': {str(e)}"
            return msg

    @staticmethod
    @add_context
    def get_dropdown_options(index: int) -> str:
        """Get all options from a native dropdown"""
        index = int(index)
        dom_element = BrowserUse.browser.selector_map[index]

        try:
            # Frame-aware approach since we know it works
            all_options = []
            frame_index = 0

            for frame in BrowserUse.browser.current_page.frames:
                try:
                    options = frame.evaluate(
                        """
                        (xpath) => {
                            const select = document.evaluate(xpath, document, null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            if (!select) return null;

                            return {
                                options: Array.from(select.options).map(opt => ({
                                    text: opt.text, //do not trim, because we are doing exact match in select_dropdown_option
                                    value: opt.value,
                                    index: opt.index
                                })),
                                id: select.id,
                                name: select.name
                            };
                        }
                    """,
                        dom_element.xpath,
                    )

                    if options:
                        formatted_options = []
                        for opt in options["options"]:
                            # encoding ensures AI uses the exact string in select_dropdown_option
                            encoded_text = json.dumps(opt["text"])
                            formatted_options.append(f"{opt['index']}: text={encoded_text}")

                        all_options.extend(formatted_options)

                except Exception:
                    pass

                frame_index += 1

            if all_options:
                msg = "\n".join(all_options)
                msg += "\nUse the exact text string in select_dropdown_option"
                return msg
            else:
                msg = "No options found in any frame for dropdown"
                return msg

        except Exception as e:
            msg = f"Error getting options: {str(e)}"
            return msg

    @staticmethod
    @add_context
    def select_dropdown_option(index: int, text: str) -> str:
        """Select dropdown option for interactive element index by the text of the option you want to select"""
        index = int(index)
        dom_element = BrowserUse.browser.selector_map[index]

        # Validate that we're working with a select element
        if dom_element.tag_name != "select":
            msg = f"Cannot select option: Element with index {index} is a {dom_element.tag_name}, not a select"
            return msg

        try:
            frame_index = 0
            for frame in BrowserUse.browser.current_page.frames:
                try:
                    # First verify we can find the dropdown in this frame
                    find_dropdown_js = """
                        (xpath) => {
                            try {
                                const select = document.evaluate(xpath, document, null,
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                                if (!select) return null;
                                if (select.tagName.toLowerCase() !== 'select') {
                                    return {
                                        error: `Found element but it's a ${select.tagName}, not a SELECT`,
                                        found: false
                                    };
                                }
                                return {
                                    id: select.id,
                                    name: select.name,
                                    found: true,
                                    tagName: select.tagName,
                                    optionCount: select.options.length,
                                    currentValue: select.value,
                                    availableOptions: Array.from(select.options).map(o => o.text.trim())
                                };
                            } catch (e) {
                                return {error: e.toString(), found: false};
                            }
                        }
                    """

                    dropdown_info = frame.evaluate(find_dropdown_js, dom_element.xpath)

                    if dropdown_info:
                        if not dropdown_info.get("found"):
                            continue

                        # "label" because we are selecting by text
                        # nth(0) to disable error thrown by strict mode
                        # timeout=1000 because we are already waiting for all network events, therefore ideally we don't need to wait a lot here (default 30s)
                        selected_option_values = (
                            frame.locator("//" + dom_element.xpath).nth(0).select_option(label=text, timeout=1000)
                        )

                        msg = f"selected option {text} with value {selected_option_values}"
                        return msg

                except Exception:
                    pass

                frame_index += 1

            msg = f"Could not select option '{text}' in any frame"
            return msg

        except Exception as e:
            msg = f"Selection failed: {str(e)}"
            return msg
