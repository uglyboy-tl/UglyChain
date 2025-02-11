from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property

from playwright.sync_api import Browser as PlaywrightBrowser
from playwright.sync_api import BrowserContext, Playwright, sync_playwright


class BrowserError(Exception):
    """Base class for all browser errors"""


class URLNotAllowedError(BrowserError):
    """Error raised when a URL is not allowed"""


@dataclass
class Browser:
    _playwright: Playwright = field(init=False)

    def start(self) -> None:
        self._playwright = sync_playwright().start()

    def stop(self) -> None:
        self._playwright.stop()

    @cached_property
    def browser(self) -> PlaywrightBrowser:
        self.start()
        return self._playwright.chromium.launch(headless=False)

    @cached_property
    def context(self) -> BrowserContext:
        if len(self.browser.contexts) > 0:
            context = self.browser.contexts[0]
        else:
            context = self.browser.new_context(no_viewport=False, java_script_enabled=True)
        context.add_init_script(
            """
			// Webdriver property
			Object.defineProperty(navigator, 'webdriver', {
				get: () => undefined
			});

			// Languages
			Object.defineProperty(navigator, 'languages', {
				get: () => ['en-US']
			});

			// Plugins
			Object.defineProperty(navigator, 'plugins', {
				get: () => [1, 2, 3, 4, 5]
			});

			// Chrome runtime
			window.chrome = { runtime: {} };

			// Permissions
			const originalQuery = window.navigator.permissions.query;
			window.navigator.permissions.query = (parameters) => (
				parameters.name === 'notifications' ?
					Promise.resolve({ state: Notification.permission }) :
					originalQuery(parameters)
			);
			(function () {
				const originalAttachShadow = Element.prototype.attachShadow;
				Element.prototype.attachShadow = function attachShadow(options) {
					return originalAttachShadow.call(this, { ...options, mode: "open" });
				};
			})();
			"""
        )
        return context
