# 结构化输出

结构化输出是 LLM 可以从对话机器人变成可实际使用的工具的一个重要能力。它可以让 LLM 返回的结果，直接转换为 Python 对象（或任何其他语言所需要的结构），从而可以直接使用。

## 实现

### 通过 Prompt 实现

绝大部分模型默认都不支持结构化输出，这也是利用 LLM 解决真实场景问题时，最大的难点之一。但是，我们可以通过一些技巧，来实现结构化输出。

一般来说，对于大部分的模型，我们是通过构造一个特定的 prompt 来实现结构化输出的。这个 prompt 会将用户的输入转换为一个特定的格式，然后再将这个格式传递给模型，从而实现结构化输出。

````text

The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Here is the output schema:

```
{schema}
```

Ensure the response can be parsed by Python json.loads
````

### 添加参数

对新版的 OpenAI 接口，已经支持了通过参数约定返回结果格式的功能。但是这种方法依然要求用户在 Prompt 中提前约定好返回结果的格式，参数只是保证返回结果的格式结构正确，而不限定格式的样式。

我们已经对支持的模型进行了适配。

### 通过 Function Call 实现

对于部分模型，我们可以通过调用模型的 Function Call 接口，来实现结构化输出。这种方法可以让模型直接返回 Python 对象，从而可以直接使用。

相关功能可以通过底层模型的 `use_native_tools` 参数来控制。
