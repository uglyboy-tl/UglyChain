# Built-in Tools

## execute_command
- Executes shell commands
- Returns command output
- Example:
  ```python
  from uglychain.tools import execute_command

  @tool
  def update_system():
      return execute_command("sudo apt update && sudo apt upgrade -y")
  ```

## web_search
- Performs web searches
- Returns search results
- Example:
  ```python
  from uglychain.tools import web_search

  @tool
  def search_weather(city: str):
      return web_search(f"Weather in {city}")
  ```

## file_operations
- Provides file system operations
- Includes read/write/delete functions
- Example:
  ```python
  from uglychain.tools import file_operations

  @tool
  def create_file(path: str, content: str):
      return file_operations.write(path, content)
  ```

## Custom Tools
- Create custom tools using @tool decorator
- Example:
  ```python
  from uglychain import tool

  @tool
  def custom_tool(param: str):
      return f"Processed {param}"
