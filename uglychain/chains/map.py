#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

from loguru import logger
from pathos.multiprocessing import ProcessingPool as Pool

from uglychain.llm import ParseError

from .llm import LLM, FunctionCall, GenericResponseType


@dataclass
class MapChain(LLM[GenericResponseType]):
    prompt_template: str = "{map_key}"
    is_init_delay: bool = field(init=False, default=True)
    map_keys: List[str] = field(default_factory=lambda: ["map_key"])

    def _validate_inputs(self, inputs: Dict[str, Any]) -> None:
        self.num = len(inputs[self.map_keys[0]])
        for map_key in self.map_keys:
            self._validate_map_key(map_key, inputs)
        super()._validate_inputs(inputs)

    def _validate_map_key(self, map_key, inputs):
        assert (
            map_key in self.input_keys and isinstance(inputs[map_key], List) and len(inputs[map_key]) == self.num
        ), f"MapChain expects {map_key} to be a list of strings with the same length"

    def _call(self, inputs: Dict[str, Any]) -> List[Union[GenericResponseType, str]]:
        inputs_list = self._generate_inputs_list(inputs)

        with Pool() as pool:
            response = pool.map(self._map_func(inputs), inputs_list)

        results = self._process_results(response)

        return results

    def _generate_inputs_list(self, inputs):
        return [
            {
                **{map_key: inputs[map_key][i] for map_key in self.map_keys},
                **{"index": i},
            }
            for i in range(self.num)
        ]

    def _map_func(self, inputs):
        def func(input) -> Dict[str, Union[int, str, GenericResponseType]]:
            new_input: Dict = {k: v for k, v in inputs.items() if k not in self.map_keys}
            new_input.update({mapping_key: input[mapping_key] for mapping_key in self.map_keys})
            prompt = self.prompt.format(**new_input)
            max_retries = 3  # 设置最大重试次数
            attempts = 0  # 初始化尝试次数
            while attempts < max_retries:
                try:
                    response = self.llm.generate(prompt, self.response_model, self.tools, self.stop)
                    if self.response_model:
                        instructor_response = self.llm.parse_response(response, self.response_model).model_dump_json()
                        if self.memory_callback:
                            self.memory_callback((prompt, response))
                        logger.debug(f"MapChain: {input['index']} finished")
                        return {"index": input["index"], "result": instructor_response}
                    elif self.tools:
                        instructor_response = self.llm.parse_response(response, FunctionCall).model_dump_json()
                        if self.memory_callback:
                            self.memory_callback((prompt, response))
                        return {"index": input["index"], "result": instructor_response}  # type: ignore
                    else:
                        if self.memory_callback:
                            self.memory_callback((prompt, response))
                        logger.debug(f"MapChain: {input['index']} finished")
                        return {"index": input["index"], "result": response}
                except ParseError as e:  # 捕获所有异常
                    attempts += 1  # 尝试次数增加
                    logger.warning(f"解析失败，第 {attempts} 次尝试重新解析")
                    logger.trace(f"第 {attempts} 次尝试解析失败，原因：{e}")
                    if attempts == max_retries:
                        return {
                            "index": input["index"],
                            "result": "Error",
                        }  # 如果达到最大尝试次数，则抛出最后一个异常
                except Exception as e:
                    logger.warning(f"MapChain: {input['index']} failed with error: {e}")
                    return {"index": input["index"], "result": "Error"}
            return {"index": input["index"], "result": "Error"}

        return func

    def _process_results(self, results) -> List[Union[GenericResponseType, str]]:
        results = sorted(results, key=lambda x: x["index"])
        if self.response_model:
            new_results = []
            for result in results:
                if result["result"] == "Error":
                    new_results.append(result["result"])
                else:
                    new_results.append(self.response_model.model_validate_json(result["result"]))
            return new_results
        else:
            return [result["result"] for result in results]
