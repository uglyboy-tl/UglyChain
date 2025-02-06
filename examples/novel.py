from __future__ import annotations

import random

from pydantic import BaseModel, Field

from uglychain import config, llm


class NovelDetail(BaseModel):
    """
    我需要你写：
    1. 输出段落：小说的下一个段落。输出段应包含约20句话，并应遵循输入指示。
    2. 输出记忆： 更新后的记忆。你应该首先解释输入记忆中的哪些句子不再需要，为什么，然后解释需要添加到记忆中的内容，为什么。之后，你应该写出更新的记忆。除了你之前认为应该删除或添加的部分，更新后的记忆应该与输入的记忆相似。更新后的记忆应该只存储关键信息。更新后的记忆不应该超过20个句子！
    3. 输出指令：接下来要写什么的指令（在你写完之后）。你应该输出3个不同的指令，每个指令都是故事的一个可能的有趣的延续。每个输出指令应该包含大约5个句子
    注意除格式要求的字段名外，其他内容请使用中文进行文本输出。

    非常重要！! 更新的内存应该只存储关键信息。更新后的记忆不应该包含超过500个字！！！！
    最后，记住你在写一本小说。像小说家一样写作，在写下一段的输出指令时不要走得太快。记住，这一章将包含10多段，而小说将包含100多章。而这仅仅是个开始。就要写一些接下来会发生的有趣的职员。另外，在写输出说明时，要考虑什么情节能吸引普通读者。
    """

    paragraph: str = Field(..., description="string of output paragraph, around 20 sentences.")
    rational: str = Field(..., description="string that explain how to update the memory")
    memory: str = Field(..., description="string of updated memory, around 10 to 20 sentences")
    instructions: list[str] = Field(..., description="list of instructions, each instruction is around 5 sentences.")


class Novel(BaseModel):
    """
    准确遵循以下格式：
    以小说的名称开始。
    接下来，写出第一章的大纲。大纲应描述小说的背景和开头。
    根据你的提纲写出前三段，并说明小说的内容。用小说的风格来写，慢慢地设置场景。
    写一个摘要，抓住这三段的关键信息。
    最后，写出三个不同的指示，说明接下来要写什么，每个指示包含大约五句话。每个指示都应该提出一个可能的、有趣的故事的延续。
    输出格式应遵循这些准则：
    名称： <小说的名称>
    概述： <第一章的大纲>
    段落1： <第1段的内容>
    段落2： <第2段的内容>
    段落3： <第3段的内容>
    总结： <摘要的内容>。
    指令1： <指令1的内容>
    指令2： <指令2的内容>
    指令3：<指令3的内容>

    请务必准确无误，并严格遵守输出格式。
    """

    title: str = Field(description="小说的名称")
    outline: str = Field(description="第一章的大纲。大纲应描述小说的背景和开头")
    paragraphs: list[str] = Field(
        description="根据你的提纲写出前三段，并说明小说的内容。用小说的风格来写，慢慢地设置场景。每一段应包含约20句话"
    )
    summary: str = Field(description="小说的摘要，大概有10到20句话, 抓住前三段的关键信息")
    instructions: list[str] = Field(description="三个不同的指示，说明接下来要写什么，每个指示包含大约五句话")


@llm(response_format=NovelDetail, need_retry=True)
def novel(short_memory: str, input_paragraph: str, instruction: str, related_paragraphs: list[str]) -> None:
    """我需要你帮我写一部小说。现在我给你一个400字的记忆（简短的总结），你应该用它来储存已经写过的关键内容，这样你就可以跟踪很长的上下文。每次，我会给你你当前的记忆（前面故事的简短总结。你应该用它来储存已经写过的关键内容，这样你就可以跟踪很长的上下文），之前写的段落，以及关于下一段要写什么的指示。"""
    pass


@llm(response_format=Novel, need_retry=True)
def init(novel_type: str, description: str) -> str:
    """你将写一部小说，有50个章节。"""
    return f"请写一篇{novel_type}的小说{description}"


def select_instruction(instructions: list[str]) -> str:
    return instructions[random.randint(0, len(instructions) - 1)]


def search(instruction: str, paragraphs: list[str]):
    return []


if __name__ == "__main__":
    # config.verbose = True
    novel_paragraphs: list[str] = []
    first = init(novel_type="青春伤痛文学", description="七月与安生")
    print(f"名称: {first.title}")
    print(f"概述: {first.outline}")
    print("======")
    for paragraph in first.paragraphs:
        print(paragraph)
        novel_paragraphs.append(paragraph)
    print("======")
    instruction = select_instruction(first.instructions)
    new = novel(
        first.summary,
        input_paragraph=first.paragraphs[-1],
        instruction=instruction,
        related_paragraphs=search(instruction, novel_paragraphs),
    )
    while True:
        if new.paragraph:
            print(new.paragraph)
            novel_paragraphs.append(new.paragraph)
            print("======")
            instruction = select_instruction(new.instructions)
            new = novel(
                new.memory,
                input_paragraph=new.paragraph,
                instruction=instruction,
                related_paragraphs=search(instruction, novel_paragraphs),
            )
        else:
            break
