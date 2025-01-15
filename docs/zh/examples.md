# Examples

## Basic LLM Usage

```python
from uglychain import llm

@llm(model="openai:gpt-4o-mini", temperature=0.1)
def hello(world: str):
    """You are a helpful assistant that writes in lower case."""
    return f"Say hello to {world[::-1]} with a poem."

hello("sama")
```

## Structured Output

```python
from pydantic import BaseModel
from uglychain import llm

class UserDetail(BaseModel):
    name: str
    age: int

@llm("openai:gpt-4o-mini", response_format=UserDetail)
def test(name: str):
    return f"{name} is a boy"

test("Bob")
```

## MapChain (Batch Processing)

```python
@llm("openai:gpt-4o-mini", map_keys=["input"])
def map(input: list[str]):
    return input

input = [
    "How old are you?",
    "What is the meaning of life?",
    "What is the hottest day of the year?",
]
for item in map(input):
    print(item)
```

## ReActChain (Tool Usage)

```python
from uglychain import react
from examples.utils import execute_command

@react("openai:gpt-4o-mini", tools=[execute_command])
def update():
    return "Update my computer system"

update()  # Automatically runs shell commands to update the system
```

## Advanced MapChain Example

```python
class AUTHOR(BaseModel):
    name: str = Field(..., description="Name")
    introduction: str = Field(..., description="Introduction")

@llm("openai:gpt-4o-mini", map_keys=["book"], response_format=AUTHOR)
def map(book: list[str], position: str):
    return f"Who is the {position} of {book}?"

input = [
    "Dream of the Red Chamber",
    "Journey to the West",
    "Romance of the Three Kingdoms",
    "Water Margin",
]
map(book=input, position="author")  # Returns a list of AUTHOR objects
