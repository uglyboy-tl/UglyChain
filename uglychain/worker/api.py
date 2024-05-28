from dataclasses import dataclass

import frontmatter

from uglychain import LLM

from .base import BaseWorker


@dataclass
class APIWorker(BaseWorker):
    output_format: str = "{result}"

    def run(self, *args, **kwargs):
        result = self._ask(*args, **kwargs)
        return self.output_format.format(result=result)

    @classmethod
    def from_file(cls, markdown_file: str):
        """
        从 Markdown 文件中读取配置并初始化 APIWorker 对象
        """
        # 读取 Markdown 文件
        with open(markdown_file, "r", encoding="utf-8") as f:
            content = frontmatter.load(f)

        # 提取 frontmatter 信息
        metadata = content.metadata

        # 提取 Markdown 正文
        body = content.content.split("***")
        if len(body) > 2:
            raise ValueError("Markdown file must contain exactly two sections separated by '***'.")
        elif len(body) == 2:
            init_info = body[0]
            prompt = body[1]
            output_format = body[2]
        elif len(body) == 1:
            prompt = body[0]
            output_format = body[1]
        else:
            prompt = body[0]

        # 获取 System 信息
        if metadata.get("system"):
            system = metadata.get("system")

        if metadata.get("provider"):
            provider = metadata.get("provider")
            model_name = metadata.get("model")
        else:
            model = LLM.DEFAULT
        # 初始化 LLM
        llm = LLM(prompt, model, system)
        worker = cls(role=system, prompt=prompt, model=model, llm=llm, output_format=output_format)

        if metadata.get("presence_penalty"):
            worker.llm.presence_penalty = metadata.get("presence_penalty")
        if metadata.get("frequency_penalty"):
            worker.llm.frequency_penalty = metadata.get("frequency_penalty")
        if metadata.get("temperature"):
            worker.llm.temperature = metadata.get("temperature")
        if metadata.get("top_p"):
            worker.llm.top_p = metadata.get("top_p")
        if metadata.get("seed"):
            worker.llm.seed = metadata.get("seed")
        # TODO :
        # if metadata.get("max_tokens"):
        #    self.llm.max_tokens = metadata.get("max_tokens")
        return worker
