## 安装

=== "pip"

    ```bash
    pip install uglychain
    ```

=== "poetry"

    ```bash
    poetry add uglychain
    ```

### 扩展功能

如果需要下列功能，需要额外安装对应的包。

- ChatGLM: `zhipuai`
- 通义千问及其他阿里平台上的模型: `dashscope`
- Gemini: `google-generativeai`
- BM25DB: `jieba-fast`

## 路线图

### 基础能力

- [x] 增加 FunctionCall 的能力
- [ ] 增加 Memory 的能力
- [x] 增加 Chain 中快速便捷的调整模型参数的能力
- [x] 支持更多的本地部署的模型，例如 vllm, llama.cpp, ollama, etc.

### 完善 Retriever

- [ ] 完善 LlamaIndex Retriever
- [ ] 增加 Combine Retriever
- [ ] 增加 DB Retriever
- [x] 增加快捷调用默认 Retriver 的入口函数

### 完善 Worker

- [x] 完善 Storage 的存储功能
- [x] 增加 Summary 的 Worker
- [x] 增加 Classify 的 Worker
- [x] 增加 Code Interpreter 的 Worker
- [x] 增加 Planner 的 Worker
