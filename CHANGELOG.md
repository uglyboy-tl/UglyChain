## [1.3.1] - 2025-02-13
### Features
- feat(structured): YAML JSON (Uglyboy)
- feat(browser-use): 支持返回图片并优化浏览器操作 (Uglyboy)
- feat(llm): 支持图像输入并优化Prompt生成逻辑 (Uglyboy)
- feat: 添加浏览器使用示例 (Uglyboy)
- feat(工具): 添加工具类的动态属性获取方法 (Uglyboy)
- feat(tools): 添加浏览器自动化工具 (Uglyboy)

### Refactor
- refactor(代码重构): 优化配置使用和错误处理 (Uglyboy)
- refactor(llm): 重构 prompt 工具函数以支持图像输入 (Uglyboy)
- refactor(uglychain): 优化 XML 和 JSON 解析逻辑 (Uglyboy)
- refactor(tool): 重构工具注册和调用逻辑 (Uglyboy)

## [1.3.0] - 2025-02-10
### Features
- feat(core): 添加多语言支持并优化任务规划 (Uglyboy)
- feat(uglychain): 添加 prompt 文件加载功能并更新相关模块 (Uglyboy)
- feat(examples): 添加基于 RAG 的问答系统示例 (Uglyboy)

### Refactor
- refactor(uglychain): MCP XML (Uglyboy)
- refactor(task): 重构任务处理逻辑 (Uglyboy)
- refactor(task): 重构任务模块以支持流程控制和并发处理 (Uglyboy)
- refactor(uglychain): 优化代码结构和性能 (Uglyboy)
- refactor(novel): 重构小说生成代码 (Uglyboy)
- refactor(uglychain): 重构并支持 OpenRouter 模型路由 (Uglyboy)
- refactor(uglychain): 重构代码并优化功能 (Uglyboy)
- refactor/examples: 更新示例代码并调整默认语言模型 (Uglyboy)
- refactor(tools): 重构 coder 工具集 (Uglyboy)
- refactor(uglychain): 重构 Action 类并优化代码组织 (Uglyboy)
- refactor(uglychain): 重构并优化代码 (Uglyboy)

### Tests
- test: 重构测试用例并添加新测试 (Uglyboy)

### Fixes
- fix(task): 优化任务流控制并添加循环依赖检测 (Uglyboy)

## [1.2.0] - 2025-01-25
### Features
- feat(core): 新增任务执行框架 (Uglyboy)
- feat(tools): 重构工具管理和调用机制 (Uglyboy)
- feat(llm): 增加语言模型重试等待时间配置 (Uglyboy)
- feat(llm): 为 llm 装饰器添加重试机制 (Uglyboy)
- feat(examples): 重构 react.py 示例并添加新功能 (Uglyboy)
- feat/examples: 添加小说生成示例 (Uglyboy)

### Refactor
- refactor(uglychain): 重构工具相关代码并优化测试 (Uglyboy)
- refactor(tool): 修改工具调用方法并更新相关代码 (Uglyboy)
- refactor(mcp): 重构 MCP 配置生成和解析逻辑 (Uglyboy)
- refactor(novel): 重构小说生成示例 (Uglyboy)
- refactor(llm): 重构 prompt 函数处理逻辑 (Uglyboy)
- refactor(uglychain): 重构 ReAct 流程并优化日志输出 (Uglyboy)

### Tests
- test: 重构测试用例并添加新功能 (Uglyboy)
- test: 优化测试用例并添加新功能的测试 (Uglyboy)

## [1.1.0] - 2025-01-20
### Features
- feat(console): 增加函数调用日志并优化控制台输出 (Uglyboy)
- feat(交互): 增加用户确认功能并优化日志显示 (Uglyboy)

### Refactor
- refactor(uglychain): 优化类型注解和测试代码 (Uglyboy)
- refactor(uglychain): 优化 API 参数显示逻辑 (Uglyboy)
- refactor(llm): 优化 API 参数处理逻辑 (Uglyboy)
- refactor(tools): 重构工具调用和响应处理 (Uglyboy)
- refactor(dev): 优化代码结构并添加测试用例 (Uglyboy)
- refactor(console): 重构消息显示逻辑 (Uglyboy)
- refactor(代码重构): 重构工具函数和类型定义 (Uglyboy)
- refactor(llm): 重构 llm 和 react 函数 (Uglyboy)

### Tests
- test(default_tools): 添加默认工具模块的测试用例 (Uglyboy)

## [1.0.5] - 2025-01-15
### Features
- feat(uglychain): 添加 MCP 支持并优化 react 函数 (Uglyboy)
- feat(console): 优化日志输出并添加 react 流程支持 (Uglyboy)
- docs(website): 构建项目文档网站 (Uglyboy)
- docs: 添加中文版本 README 文件并更新相关内容 (Uglyboy)

### Refactor
- refactor(config): 优化 show_progress 配置 (Uglyboy)

### Tests
- test(client): 增加异常处理测试用例并添加 console 模块测试 (Uglyboy)

## [1.0.4] - 2025-01-14
### Features
- ci(release): 增加版本更新检查 (Uglyboy)
- ci: 更新 release workflow 权限设置 (Uglyboy)
- ci: 更新 GitHub Actions 工作流 (Uglyboy)
- ci: 更新 GitHub Actions 工作流以发布到 PyPI (Uglyboy)
- docs: 添加 README.md 文件并更新工作流 (Uglyboy)
- ci: 添加测试工作流 (Uglyboy)

### Fixes
- Bump version to 1.0.4 (github-actions[bot])

## [1.0.3] - 2025-01-14
### Features
- ci(release): 更新 GitHub Actions 发布流程 (Uglyboy)
- ci(release): 优化 GitHub Actions 发布流程 (Uglyboy)
- ci(release): 更新 GitHub Actions 工作流以修复发布问题 (Uglyboy)

### Fixes
- Bump version to 1.0.3 (github-actions[bot])

## [1.0.2] - 2025-01-12
### Features
- ci(release): 简化 release workflow 并移除手动触发选项 (Uglyboy)
- ci: 添加手动触发 Release workflow 功能 (Uglyboy)
- ci(release): 更新 GitHub Actions 发布流程 (Uglyboy)
- ci(release): 优化 GitHub Actions 发布流程 (Uglyboy)
- ci(release): 添加发布工作流并更新版本号 (Uglyboy)

## [1.0.1] - 2025-01-11
### Features
- refactor(项目): 重构代码并更新版本号 (Uglyboy)

## [1.0.0] - 2025-01-07
### Features
- build(deps): 更新 pydantic 依赖版本 (Uglyboy)
- feat(react): 优化代码解析和工具执行功能 (Uglyboy)

## [0.9.0] - 2025-01-04
### Features
- feat(console): 添加工具参数日志输出 (Uglyboy)
- feat(react): 增加反应链超过最大次数时的处理机制 (Uglyboy)
- refactor(react): 重构反应式编程模型 (Uglyboy)
- refactor(uglychain): 将 validate_response_type 方法
- refactor(uglychain): 将 validate_response_type 方法改为受保护的方法 (Uglyboy)
- refactor(uglychain): 重构 structured.py 中的模型匹配逻辑 (Uglyboy)

## [0.8.0] - 2025-01-02
### Features
- feat(tools): 重构工具调用功能 (Uglyboy)
