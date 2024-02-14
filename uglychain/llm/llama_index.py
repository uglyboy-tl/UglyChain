from typing import Any

from pydantic.v1 import Field, root_validator

try:
    from llama_index.core.llms import (
        CompletionResponse,
        CompletionResponseGen,
        CustomLLM,
        LLMMetadata,
    )
    from llama_index.core.llms.callbacks import llm_completion_callback
except ImportError as err:
    raise ImportError("Please install the `llama-index-core` package to use this LLM.") from err

from uglychain.provider import Model, get_llm_provider

from .base import BaseLanguageModel


class LlamaIndexLLM(CustomLLM):
    model: Model = Model.DEFAULT
    llm: BaseLanguageModel = Field(init=False, default=None)

    @root_validator(pre=False, skip_on_failure=True)
    def create_llm(cls, values):
        model_name = values.get("model")
        values["llm"] = get_llm_provider(model_name)
        return values

    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata."""
        if hasattr(self.llm, "MAX_TOKENS"):
            context_window = self.llm.MAX_TOKENS  # type: ignore
        else:
            context_window = 4096
        return LLMMetadata(
            context_window=context_window,
            is_chat_model=True,
            model_name=self.llm.model,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        response = self.llm.generate(prompt)
        return CompletionResponse(text=response)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        response = ""
        dummy_response = self.llm.generate(prompt)
        for token in dummy_response:
            response += token
            yield CompletionResponse(text=response, delta=token)
