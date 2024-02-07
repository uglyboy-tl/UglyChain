# Code Interpreter

Code Interpreter 最早是 ChatGPT 官方提供的功能插件，可以在聊天中根据用户的描述，自主选择是否用代码解释器来帮助回答问题，从而让大模型可以更好的解答很多计算类或数据类的问题。

而在业务场景中，代码解释器也是让 LLM 拥有解决具体问题能力的最重要的工具之一。所以在我们提供的 Worker 中，我们也提供了代码解释器的功能。

## 代码解释器的实现原理

参见 [ReAct](../Agent/react.md/#_3) 的实现原理。

## 代码解释器的使用

```python
worker = CodeInterpreter(model=Model.YI)
worker.run("更新系统软件包")
```

## 代码解释器的优化

如果对于编写的代码有更具体的要求，可以在 `Worker` 的 role 中设定具体的要求。

## 代码解释器中代码执行部分的实现

我们参考了 [Open Interpreter](https://github.com/KillianLucas/open-interpreter) 的实现方式，将代码解释器的执行部分独立出来，作为一个独立的工具，并去掉了生成图表等功能（工程化实现里不需要图片作为上下文交互信息的方式）。
