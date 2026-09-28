"""
01 · Your first tool call.  (NEW · your first Week 2 build)

Week 1 recap: our agents produced text like  ACTION: calculator[23*7]  and we
parsed it with a regex. That works, but it is brittle — the model can misformat
the line, add prose, or invent a tool. Modern providers solve this with native
FUNCTION (TOOL) CALLING: you describe your tools as JSON schemas, and the model
replies with a STRUCTURED, VALIDATED request — no string parsing.

Goal of this lesson — one clean round-trip with ONE tool:
    describe the tool  ->  model chooses it & fills the arguments
    ->  we run it       ->  we return the result  ->  model writes the answer.

-------------------------------------------------------------------
YOUR TASKS
  TODO 1 · write the tool SCHEMA for get_weather (name, description, one
           required string parameter `city`).
  TODO 2 · run each requested tool and append its result to `messages`
           (remember the tool_call_id).
-------------------------------------------------------------------
Run it:  python skeleton/01_first_tool_call.py
Stuck?   trainer/01_first_tool_call.py has the full version.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.llm_client import LLMClient

# The tool itself — an ordinary Python function.
def get_weather(city: str):
    """A pretend weather API. In Lab 04 we'll call a real one."""
    fake = {"dubai": "38C and sunny", "london": "14C and rainy",
            "tokyo": "22C and cloudy"}
    return fake.get(city.strip().lower(), "unknown city")


# TODO 1: describe the tool to the model.
#   Shape:
#   TOOLS = [{
#       "type": "function",
#       "function": {
#           "name": "get_weather",
#           "description": "<when should the model use this?>",
#           "parameters": {
#               "type": "object",
#               "properties": { "city": {"type": "string", "description": "..."} },
#               "required": [ ... ],
#           },
#       },
#   }]
TOOLS = []  # TODO 1: replace with the schema above


def main():
    client = LLMClient()
    messages = [{"role": "user", "content": "What's the weather in Dubai right now?"}]

    # Turn 1 — the model reads the tools and decides what to call.
    result = client.chat(messages, tools=TOOLS)

    if not result.wants_tools:
        print("Model answered without a tool:", result.text)
        print("(If TOOLS is still empty, do TODO 1.)")
        return

    # Record the model's message so the conversation stays consistent.
    messages.append(result.raw_message)

    # TODO 2: for each call in result.tool_calls:
    #   - print what the model wants
    #   - run get_weather(**call.arguments)
    #   - append {"role": "tool", "tool_call_id": call.id, "content": str(result)}
    for call in result.tool_calls:
        pass  # TODO 2

    # Turn 2 — the model turns the tool result into a natural answer.
    final = client.chat(messages, tools=TOOLS)
    print("\nFINAL:", final.text)


if __name__ == "__main__":
    main()
