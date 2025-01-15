# Configuration Guide

## Environment Variables

### Required Variables
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- more can be found in [aisuite](https://github.com/andrewyng/aisuite)

## Configuration File
not implemented yet

## Runtime Configuration

Override configuration at runtime:

```python
from uglychain import config
config.verbose = True # Enable verbose logging
config.use_parallel_processing = True # Enable parallel processing
config.show_progress = False # Disable progress bar
config.default_api_params = {
    "temperature": 0.1,
    "max_tokens": 1000
    # ... other default parameters
}
```
