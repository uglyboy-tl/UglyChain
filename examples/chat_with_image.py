from __future__ import annotations

from uglychain import config, llm


@llm
def test(prompt: str):
    return str(prompt)


if __name__ == "__main__":
    config.verbose = True
    test("图片里有几个人？", image="https://imagepphcloud.thepaper.cn/pph/image/332/567/397.jpg")  # type: ignore
