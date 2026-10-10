"""
00 · Architecture setup check.  (run this FIRST in Week 3)

Week 3 builds reasoning architectures (ReAct, planning, reflection) on top of
the Week 2 tool-calling engine. Nothing new to install — this just confirms:
  1. Your provider supports native tool calling (openai / groq / ollama), and
  2. The agent can take MORE THAN ONE step to reach an answer (call a tool,
     read the result, then call another) — which is what every ReAct loop does.

If this prints a FINAL answer saying Dubai is hotter, you're ready for Lab 1.

Run it:
    python skeleton/00_arch_setup_check.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.llm_client import LLMClient

# A deterministic, offline "weather" tool — no API key, no network.
FAKE_WEATHER = {"dubai": 38, "london": 14, "tokyo": 22, "mumbai": 33}

def get_temperature(city: str):
    t = FAKE_WEATHER.get(city.strip().lower())
    return f"{t}" if t is not None else f"error: no reading for '{city}'"

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_temperature",
        "description": "Get the current temperature in Celsius for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "e.g. 'Dubai'"}},
            "required": ["city"],
        },
    },
}]


def main():
    client = LLMClient()
    print(f"Provider: {client.provider}  |  Model: {client._default_model()}")
    if client.provider not in ("openai", "groq", "ollama"):
        print("Week 3 uses native tool calling — set LLM_PROVIDER=groq (free), openai or ollama.")
        return

    messages = [{"role": "user",
                 "content": "Which is hotter right now, Dubai or London? "
                            "Use the tool for each city, then tell me."}]

    # A tiny multi-step loop (the shape Lab 1 formalises as ReAct).
    for step in range(1, 6):
        result = client.chat(messages, tools=TOOLS)
        if not result.wants_tools:
            print("FINAL:", result.text)
            print("\nSetup OK — multi-step tool calling works. On to Lab 1 (ReAct).")
            return
        messages.append(result.raw_message)
        for call in result.tool_calls:
            out = get_temperature(**call.arguments)
            print(f"  step {step}: {call.name}({call.arguments}) -> {out}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(out)})

    print("Stopped: reached the step limit (unexpected for this simple task).")


if __name__ == "__main__":
    main()
