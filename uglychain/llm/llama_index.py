from typing import Any

from llama_index.core.llms import (
    CompletionResponse,
    CompletionResponseGen,
    CustomLLM,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback

from .base import BaseLanguageModel


class LlamaIndexLLM(CustomLLM):
    llm: BaseLanguageModel

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
