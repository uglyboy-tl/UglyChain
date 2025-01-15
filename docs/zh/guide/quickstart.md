# Quick Start

## Installation

Install using pdm:

```bash
pdm add uglychain
```

## Basic Usage

### llm Decorator

```python
from uglychain import llm

@llm(model="openai:gpt-4o-mini", temperature=0.1)
def hello(world: str):
    """You are a helpful assistant that writes in lower case."""
    return f"Say hello to {world[::-1]} with a poem."

response = hello("sama")
print(response)
```

### Structured Output

```python
from pydantic import BaseModel
from uglychain import llm

class UserDetail(BaseModel):
    name: str
    age: int

@llm(model="openai:gpt-4o-mini", response_format=UserDetail)
def parse_user(name: str):
    return f"{name} is a boy"

user = parse_user("Bob")
print(user)
```

### MapChain (Batch Processing)

```python
@llm(model="openai:gpt-4o-mini", map_keys=["input"])
def batch_process(input: list[str]):
    return input

inputs = [
    "How old are you?",
    "What is the meaning of life?",
    "What is the hottest day of the year?",
]

for result in batch_process(inputs):
    print(result)
```

### ReActChain (Tool Usage)

```python
from uglychain import react
from examples.utils import execute_command

@react(model="openai:gpt-4o-mini", tools=[execute_command])
def update_system():
    return "Update my computer system"

update_system()  # Automatically runs system update commands
```

## Configuration
The API Keys can be set as environment variables, or can be passed as config to the aisuite Client constructor. You can use tools like python-dotenv 或 direnv to set the environment variables manually.

```shell
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```
