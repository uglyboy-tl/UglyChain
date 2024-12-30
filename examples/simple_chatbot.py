from __future__ import annotations

from uglychain import config, llm


@llm(model="openai:gpt-4o-mini", temperature=0.7)
def chat_bot(message_history: list):
    "You are a friendly chatbot. Engage in casual conversation."
    return message_history


message_history = []
config.show_progress = False
# config.verbose = True
while True:
    user_input = input("You: ")
    message_history.append({"role": "user", "content": user_input})
    response = chat_bot(message_history)
    print("Bot:", response)
    message_history.append({"role": "assistant", "content": response})
