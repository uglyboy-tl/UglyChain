import sys
from enum import Enum
from typing import Callable, List

from loguru import logger
from pydantic import BaseModel

from uglychain import LLM, Model
from uglychain.chains.react_new import ReActChain, finish
from uglychain.llm.tools import ActionResopnse, FunctionCall, tools_schema

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")


class Done(BaseModel):
    thought: str
    final_answer: str


def call(tools: List[Callable], response: FunctionCall):
    for tool in tools:
        if tool.__name__ == response.name:
            return tool(**response.args)
    raise ValueError(f"Can't find tool {response.name}")


class Unit(Enum):
    FAHRENHEIT = "fahrenheit"
    CELSIUS = "celsius"


def get_current_weather(location: str, unit: Unit = Unit.FAHRENHEIT) -> str:
    """Get the current weather in a given location.

    Args:
        location (str): The city and state, e.g., San Francisco, CA
        unit (Unit): The unit to use, e.g., fahrenheit or celsius
    """
    return "晴天，25华氏度"


def search_baidu(query: str) -> str:
    """Search Baidu for the query.

    Args:
        query (str): The query to search.
    """
    return "牛顿出生于1642年"


def search_google(query: str) -> str:
    """Search Google for the query.

    Args:
        query (str): The query to search.
    """
    return "牛顿出生于2000年"


def search_bing(query: str) -> str:
    """Search Bing for the query.

    Args:
        query (str): The query to search.
    """
    return f"{query}是一个技术博主"


REACT = """
Assistant is a large language model trained by OpenAI.

Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

TOOLS:
------

Assistant has access to the following tools:

{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

Begin!

New input: {input}
{history}
"""


def llm(model: Model | None = None):
    if model:
        llm = LLM(model=model)
    else:
        llm = LLM()
    response = llm("Hi!")
    logger.info(response)


def base_react(model: Model | None = None):
    tools: List[Callable] = [finish, get_current_weather, search_baidu]
    tool_names = [tool.__name__ for tool in tools]
    # instructor = Instructor.from_BaseModel(FunctionCall)
    # instructor_prompt = instructor.get_format_instructions()
    if model:
        llm = LLM(REACT, model=model)
    else:
        llm = LLM(REACT)
    response = llm(
        tools=tools_schema(tools),
        input="What's the weather in San Francisco?",
        history="Thought: I need to use the get_current_weather tool to get the current weather in San Francisco.\nAction: get_current_weather\nAction Input: {'location': 'San Francisco, CA', 'unit': 'FAHRENHEIT'}\nObservation: 晴天，25华氏度",
        tool_names=tool_names,
    )
    logger.success(response)
    if model:
        llm1 = LLM(model=model,response_model=ActionResopnse)
    else:
        llm1 = LLM(response_model=ActionResopnse)
    logger.success(llm1(response))


def react(model: Model | None = None):
    tools: List[Callable] = [get_current_weather, search_baidu]
    if model:
        llm = ReActChain(model=model, tools=tools)
    else:
        llm = ReActChain(tools=tools)

    # response = llm("牛顿生于哪一年")
    response = llm("What's the weather in San Francisco?")
    logger.info(response)


if __name__ == "__main__":
    # llm(Model.GEMINI)
    base_react(Model.YI_32K)
    # react(Model.GPT3_TURBO)
