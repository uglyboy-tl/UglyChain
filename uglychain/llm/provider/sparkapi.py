import base64
import hashlib
import hmac
import json
import textwrap
from dataclasses import dataclass
from datetime import datetime
from email.utils import formatdate
from typing import Any, Callable, Dict, List, Optional, Type, Union
from urllib.parse import urlencode, urlparse

from loguru import logger
from pydantic import BaseModel

from uglychain.llm.base import BaseLanguageModel
from uglychain.utils import config, retry_decorator


@dataclass
class SparkAPI(BaseLanguageModel):
    model: str = "v3.5"
    api_url = f"wss://spark-api.xf-yun.com/{model}/chat"

    def generate(
        self,
        prompt: str = "",
        response_model: Optional[Type[BaseModel]] = None,
        tools: Optional[List[Callable]] = None,
        stop: Union[Optional[str], List[str]] = None,
    ) -> str:
        kwargs = self.get_kwargs(prompt, response_model, tools, stop)
        response = self.completion_with_backoff(**kwargs)
        logger.trace(f"kwargs:{kwargs}\nresponse:{response}")
        return response

    def get_kwargs(
        self,
        prompt: str,
        response_model: Optional[Type[BaseModel]],
        tools: Optional[List[Callable]],
        stop: Union[Optional[str], List[str]],
    ) -> Dict[str, Any]:
        kwargs = super().get_kwargs(prompt, response_model, tools, stop)
        kwargs.pop("stop")
        messages = kwargs.pop("messages")
        kwargs["payload"] = {"message": {"text": messages}}
        return kwargs

    @property
    def default_params(self) -> Dict[str, Any]:
        options = {"temperature": self.temperature, "domain": f"general{self.model}"}
        kwargs = {
            "header": {
                "app_id": config.spark_app_id,
            },
            "parameter": {"chat": options},
        }
        return kwargs

    def _create_client(self):
        try:
            from websockets.sync.client import connect as ws_connect
        except ImportError as err:
            raise ImportError("You need to install `pip install sparkapi-python` to use this provider.") from err
        _client = ws_connect(self._get_wss_url())
        return _client

    @retry_decorator()
    def completion_with_backoff(self, **kwargs):
        return "".join(self._get_completion_from_messages(**kwargs))

    def _get_completion_from_messages(self, **kwargs):
        self.client.send(json.dumps(kwargs, ensure_ascii=False))
        while True:
            res = json.loads(self.client.recv())
            if res["header"]["status"] == 2:
                break
            content = res["payload"]["choices"]["text"][0]["content"]
            yield content

    @property
    def max_tokens(self):
        return 2000

    def _get_wss_url(self):
        """
        Generate auth params for API request.
        """
        api_host = urlparse(self.api_url).netloc
        api_path = urlparse(self.api_url).path

        # step1: generate signature
        rfc1123_date = self._generate_rfc1123_date()
        signature_origin = textwrap.dedent(
            f"""
            host: {api_host}
            date: {rfc1123_date}
            GET {api_path} HTTP/1.1
        """
        ).strip()
        signature_sha = hmac.new(
            config.spark_api_secret.encode(), signature_origin.encode(), digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode()

        # step2: generate authorization
        authorization_payload = {
            "api_key": config.spark_api_key,
            "algorithm": "hmac-sha256",
            "headers": "host date request-line",
            "signature": signature_sha_base64,
        }
        authorization_origin = ", ".join(f'{k}="{v}"' for k, v in authorization_payload.items())
        authorization = base64.b64encode(authorization_origin.encode()).decode()

        # step3: generate wss url
        payload = {"authorization": authorization, "date": rfc1123_date, "host": api_host}
        url = self.api_url + "?" + urlencode(payload)
        # print(f'wss url: {url}')
        return url

    @staticmethod
    def _generate_rfc1123_date():
        """
        Generate a RFC 1123 compliant date string.

        """
        current_datetime = datetime.now()
        timestamp = current_datetime.timestamp()
        return formatdate(timeval=timestamp, localtime=False, usegmt=True)
