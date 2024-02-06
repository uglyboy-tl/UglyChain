#!/usr/bin/env python3

from dataclasses import dataclass

import requests
from loguru import logger
from tenacity import RetryError, before_sleep_log, retry, stop_after_attempt, wait_fixed

from uglychain.utils import config

from .base import BaseRetriever

BING_SEARCH_API_URL = "https://api.bing.microsoft.com/v7.0/search"


@dataclass
class BingRetriever(BaseRetriever):
    def __post_init__(self):
        assert hasattr(config, "bing_subscription_key"), "Bing subscription key not found in config"
        assert isinstance(config.bing_subscription_key, str), "Bing subscription key should be a string"
        assert config.bing_subscription_key, "Bing subscription key should not be empty"

    def search(self, query: str, n: int = BaseRetriever.default_n) -> list[str]:
        try:
            response = self._send_request(query, n)
            json = response.json()
            results = json.get("webPages", {}).get("value", [])
            return [self._format(result) for result in results[:n]] if results else []
        except (ValueError, requests.RequestException, RetryError) as e:
            logger.error(f"Error occurred while sending request or parsing response: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        before_sleep=before_sleep_log(logger, "WARNING"),  # type: ignore
    )
    def _send_request(self, query: str, n: int):
        response = requests.get(
            BING_SEARCH_API_URL,
            headers={"Ocp-Apim-Subscription-Key": config.bing_subscription_key},
            params={"q": query, "count": n},
            timeout=5,
        )
        response.raise_for_status()
        return response

    @classmethod
    def _format(cls, result: dict) -> str:
        if not all([result.get("name"), result.get("url"), result.get("snippet")]):
            logger.error(f"Missing key in search result: {result}")
            raise KeyError("Missing key in search result")
        return f"[{result.get('name')}]({result.get('url')})\n> {result.get('snippet')}"
