"""
00 · Tool-calling setup check.  (run this FIRST in Week 2)

Confirms two things before the labs:
  1. Your provider supports native tool calling (openai / groq / ollama), and
  2. A full tool round-trip works: model asks for a tool -> we run it ->
     we hand the result back -> model gives a final answer.

If this prints a final answer that mentions 21, you're ready for Lab 1.

Run it:
    python trainer/00_tools_setup_check.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.llm_client import LLMClient

# One trivial tool the model can call.
def add(a, b):
    return a + b

TOOLS = [{
    "type": "function",
    "function": {
        "name": "add",
        "description": "Add two numbers and return the sum.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "first number"},
                "b": {"type": "number", "description": "second number"},
            },
            "required": ["a", "b"],
        },
    },
}]


def main():
    client = LLMClient()
    print(f"Provider: {client.provider}  |  Model: {client._default_model()}")

    messages = [{"role": "user",
                 "content": "What is 13 + 8? Use the add tool, then tell me the number."}]

    # Turn 1 — the model should ask to call add(13, 8).
    result = client.chat(messages, tools=TOOLS)
    if not result.wants_tools:
        print("Model did not request a tool. Reply was:", result.text)
        print("Tip: some tiny local models skip tools — try Groq (free).")
        return

    messages.append(result.raw_message)          # record what the model said
    for call in result.tool_calls:
        print(f"  model called: {call.name}({call.arguments})")
        output = add(**call.arguments)
        messages.append({"role": "tool", "tool_call_id": call.id,
                         "content": str(output)})

    # Turn 2 — hand the result back; the model writes the final answer.
    final = client.chat(messages, tools=TOOLS)
    print("FINAL:", final.text)
    print("\nSetup OK — tool calling works. On to Lab 1.")


if __name__ == "__main__":
    main()
