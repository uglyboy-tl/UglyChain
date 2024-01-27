#!/usr/bin/env python3
# -*-coding:utf-8-*-

from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

from pathos.multiprocessing import ProcessingPool as Pool
from loguru import logger

from .llm import LLM, GenericResponseType


@dataclass
class MapChain(LLM[GenericResponseType]):
    is_init_delay: bool = True
    map_keys: List[str] = field(default_factory=lambda: ["input"])

    def _validate_inputs(self, inputs: Dict[str, Any]) -> None:
        self.num = len(inputs[self.map_keys[0]])
        for map_key in self.map_keys:
            self._validate_map_key(map_key, inputs)
        super()._validate_inputs(inputs)

    def _validate_map_key(self, map_key, inputs):
        assert (
            map_key in self.input_keys
            and isinstance(inputs[map_key], List)
            and len(inputs[map_key]) == self.num
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
            new_input: Dict = {
                k: v for k, v in inputs.items() if k not in self.map_keys
            }
            new_input.update(
                {mapping_key: input[mapping_key] for mapping_key in self.map_keys}
            )
            prompt = self.prompt.format(**new_input)
            try:
                response = self.llm.generate(prompt, self.response_model)
                if self.response_model:
                    response = self.llm.parse_response(response, self.response_model).model_dump_json()
            except Exception as e:
                logger.warning(f"MapChain: {input['index']} failed with error: {e}")
                response = "Error"
            logger.debug(f"MapChain: {input['index']} finished")
            return {"index": input["index"], "result": response}

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