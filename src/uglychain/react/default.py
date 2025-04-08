from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Literal

from uglychain.config import config
from uglychain.llm import gen_prompt, llm
from uglychain.schema import Messages, P, T
from uglychain.utils import retry

from .action import Action
from .base import BaseReActProcess
from .prompt import REACT_SYSTEM_PROMPT


@dataclass
class ReActProcess(BaseReActProcess[T]):
    @cached_property
    def react(self) -> Callable[..., Action]:
        tools_names = [f"`{tool.name}`" for tool in self.tools]

        def react_once(*prompt_args: P.args, acts: Sequence[Action], **prompt_kwargs: P.kwargs):  # type: ignore
            message = gen_prompt(self.func, *prompt_args, **prompt_kwargs)
            if isinstance(message, list):
                if acts:
                    message.append({"role": "assistant", "content": str(acts[-1])})
                return message
            elif isinstance(message, str):
                return message + "\n" + "\n".join(str(a) for a in acts) + "\n" + "Thought:"
            else:
                raise ValueError("Invalid output type")

        react_once.__doc__ = REACT_SYSTEM_PROMPT.format(
            tools_names=", ".join(tools_names),
            tools_descriptions=self.tools_descriptions,
            extra_instructions=self.func.__doc__ if self.func.__doc__ else "",
            language=config.default_language,
        )

        @retry(n=config.llm_max_retry, timeout=config.llm_timeout, wait=config.llm_wait_time)
        def react_response_action_with_retry(*args: Any, **kwargs: Any) -> Action:
            result = llm(
                model=self.model,
                session=self.session,
                map_keys=None,
                response_format=None,
                n=None,
                tools=None,
                stop=["Observation:"],
                **self.api_params,
            )(react_once)(*args, **kwargs)
            if isinstance(result, Iterator):
                result = "".join(result)
            act = Action.from_response(result)
            self.session.send("action", act.thought, style="yellow")
            return act

        return react_response_action_with_retry

    @cached_property
    def final(self) -> Callable[..., str | Iterator[str] | T]:
        def final_call(
            *prompt_args: Any,
            acts: Sequence[Action],
            call_type: Literal["failed", "trans"],
            **prompt_kwargs: Any,
        ) -> str | Messages:
            system_prompt = (
                "An agent attempted to solve the user's task but encountered difficulties and failed. Your task is to provide the final answer instead.\n"
                if call_type == "failed"
                else "An agent has completed the user's task and now needs to convert the final answer into a new output format.\n"
            )
            message = gen_prompt(self.func, *prompt_args, **prompt_kwargs)
            memory = "\n".join(str(a) for a in acts)
            if isinstance(message, list):
                return [
                    {"role": "system", "content": system_prompt},
                    *message,
                    {"role": "assistant", "content": str(acts[-1])},
                    {
                        "role": "user",
                        "content": "Based on the information above, please provide a response to the user's request.",
                    },
                ]
            elif isinstance(message, str):
                return f"{system_prompt}\nHere is the agent's memory:\n-----{message}\n{memory}\n-----\n Based on the information above, please provide a response to the user's request."
            else:
                raise ValueError("Invalid output type")

        llm_final_call = llm(
            self.model,
            response_format=self.response_format,
            session=self.session,
            map_keys=None,
            need_retry=True,
            n=None,
            tools=None,
            **self.api_params,
        )(final_call)

        return llm_final_call
