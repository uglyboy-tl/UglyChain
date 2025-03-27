from __future__ import annotations

from collections.abc import Iterator

from uglychain import config, llm


@llm("deepseek:deepseek-reasoner", temperature=0.7, stream=True)
def chat_bot(message_history: list[dict[str, str]]) -> list[dict[str, str]]:
    "You are a friendly chatbot. Engage in casual conversation."
    return message_history


message_history = []
# config.verbose = True
while True:
    user_input = input("You: ")
    message_history.append({"role": "user", "content": user_input})
    response = chat_bot(message_history)
    output = ""
    if isinstance(response, Iterator):
        print("Bot: ", end="", flush=True)
        for chunk in response:
            print(chunk, end="", flush=True)
            output += chunk
        print()
    else:
        output = response.split("</think>")[-1]
    message_history.append({"role": "assistant", "content": output})
