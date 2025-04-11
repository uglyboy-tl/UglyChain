from __future__ import annotations

from pydantic import BaseModel

from uglychain import config, think


# 简单使用示例
@think("openai:gpt-4o-mini")
def solve_problem(question: str):
    return f"请解答这个问题: {question}"


# 结构化输出示例
class Answer(BaseModel):
    solution: str
    explanation: str


@think(thinking_model="deepseek:deepseek-reasoner", model="openai:gpt-4o-mini", response_format=Answer)
def solve_math(problem: str):
    return f"解决这个数学问题: {problem}"


if __name__ == "__main__":
    # config.verbose = True

    # 简单示例
    result = solve_problem(
        "如果一个球从10米高的地方落下，假设每次弹起的高度是前一次的80%，那么它会弹几次才能达到不足1米的高度？"
    )
    print(result)

    # 结构化输出示例
    answer = solve_math("计算 (3x^2 + 2x - 5) 在 x=2 时的值")
    print(f"Solution: {answer.solution}")
    print(f"Explanation: {answer.explanation}")
