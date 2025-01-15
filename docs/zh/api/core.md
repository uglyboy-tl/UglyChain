# Core API Overview

## Main Modules

### LLM Module
- Core functionality for interacting with language models
- Supports multiple model providers (OpenAI, Anthropic, etc.)
- Includes decorator-based interface for easy usage

### ReAct Module
- Implements reasoning and acting capabilities
- Supports tool usage and multi-step reasoning
- Built-in support for parallel processing

### Structured Module
- Provides structured output capabilities
- Integrates with Pydantic models
- Supports automatic schema generation

## Key Features

- **Decorator-based API**: Simplify LLM interactions with intuitive decorators
- **Structured Output**: Easily parse LLM responses into structured data
- **Parallel Processing**: Process multiple inputs concurrently
- **ReAct Support**: Built-in support for reasoning and acting
- **Extensible Architecture**: Easily add custom models and tools
