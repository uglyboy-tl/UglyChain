#!/usr/bin/env python3

from dataclasses import dataclass

import requests
from loguru import logger
from tenacity import RetryError, before_sleep_log, retry, stop_after_attempt, wait_fixed

from .base import BaseRetriever

Open_Procedures_API_URL = "https://open-procedures.replit.app/search/"


@dataclass
class OpenProceduresRetriever(BaseRetriever):
    def search(self, query: str, n: int = BaseRetriever.default_n) -> list[str]:
        try:
            response = self._send_request(query, n)
            return [response.json()["procedures"]]
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
            Open_Procedures_API_URL,
            params={"query": query},
            timeout=5,
        )
        response.raise_for_status()
        return response
