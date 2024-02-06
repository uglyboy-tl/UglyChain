#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

import requests
from loguru import logger
from tenacity import RetryError, before_sleep_log, retry, stop_after_attempt, wait_fixed

from .base import BaseRetriever

ARXIV_SEARCH_API_URL = "http://export.arxiv.org/api/query"


@dataclass
class ArxivRetriever(BaseRetriever):
    def search(self, query: str, n: int = BaseRetriever.default_n) -> List[str]:
        try:
            response = self._send_request(query, n)
            xml = response.text
            root = ElementTree.fromstring(xml)
            entries = root.findall("{http://www.w3.org/2005/Atom}entry")
            results = [self._format(entry) for entry in entries[:n]]
            return results
        except ElementTree.ParseError as e:
            logger.error(f"Error occurred while parsing XML: {e}")
            return []
        except (requests.RequestException, RetryError) as e:
            logger.error(f"Error occurred while sending request or parsing response: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        before_sleep=before_sleep_log(logger, "WARNING"),  # type: ignore
    )
    def _send_request(self, query: str, n: int):
        response = requests.get(
            ARXIV_SEARCH_API_URL,
            params={"search_query": query, "start": 0, "max_results": n},
            timeout=5,
        )
        response.raise_for_status()
        return response

    @classmethod
    def _format(cls, entry: ElementTree.Element) -> str:
        title = entry.find("{http://www.w3.org/2005/Atom}title").text  # type: ignore
        summary = entry.find("{http://www.w3.org/2005/Atom}summary").text  # type: ignore
        link = entry.find('{http://www.w3.org/2005/Atom}link[@title="pdf"]').get("href")  # type: ignore
        if not all([title, link, summary]):
            logger.error(f"Missing key in search result: {entry}")
            raise KeyError("Missing key in search result")
        return f"[{title}]({link})\n> {summary}"
