"""
03 · A reusable tool-calling agent.  (NEW · the Day-2 core build)

Labs 01–02 did a single round-trip. A real agent may need SEVERAL tool calls
before it can answer (look up two prices, then add them). This is the same
observe -> reason -> act -> evaluate loop from Week 1, but now REASON is the
provider's native tool calling and MEMORY is the `messages` list.

You'll finish the loop inside ToolAgent.run().

-------------------------------------------------------------------
YOUR TASKS  (all inside ToolAgent.run())
  TODO 1 · ask the model for the next step: self.client.chat(messages, tools=self.schemas)
  TODO 2 · if the reply has NO tool calls, it's the final answer — return it.
  TODO 3 · otherwise append result.raw_message, then for each call: run the tool
           with self._run_tool(call), print it, and append a "tool" message
           with the tool_call_id and the string result.
-------------------------------------------------------------------
Run it:  python skeleton/03_tool_calling_agent.py
Stuck?   trainer/03_tool_calling_agent.py has the full version.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.llm_client import LLMClient

MAX_STEPS = 6


class ToolAgent:
    def __init__(self, system=None):
        self.client = LLMClient()
        self.schemas = []
        self.functions = {}
        self.system = system

    def register(self, fn, schema):
        self.functions[schema["function"]["name"]] = fn
        self.schemas.append(schema)

    def _run_tool(self, call):
        fn = self.functions.get(call.name)
        if fn is None:
            return f"error: unknown tool '{call.name}'"
        try:
            return fn(**call.arguments)
        except Exception as e:
            return f"error: {call.name} failed: {e}"

    def run(self, goal):
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        messages.append({"role": "user", "content": goal})

        for step in range(1, MAX_STEPS + 1):
            # TODO 1: ask the model for its next step (pass tools=self.schemas)
            result = None  # replace this

            # TODO 2: if not result.wants_tools: return result.text

            # TODO 3: append result.raw_message, then run each tool call and
            #         append a {"role": "tool", "tool_call_id": ..., "content": ...}
            pass

        return "Stopped: reached the tool-step limit without a final answer."


# ---- tools for the demo (given) ----
CATALOGUE = {"widget": 25, "gadget": 40, "sprocket": 12}

def get_price(item: str):
    price = CATALOGUE.get(item.strip().lower())
    return price if price is not None else f"error: no price for '{item}'"

def add(a: float, b: float):
    return a + b

PRICE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_price",
        "description": "Get the catalogue price of one item in USD.",
        "parameters": {
            "type": "object",
            "properties": {"item": {"type": "string"}},
            "required": ["item"],
        },
    },
}
ADD_SCHEMA = {
    "type": "function",
    "function": {
        "name": "add",
        "description": "Add two numbers.",
        "parameters": {
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"],
        },
    },
}


if __name__ == "__main__":
    agent = ToolAgent(system="You are a helpful assistant. Use tools when needed; "
                             "take one step at a time.")
    agent.register(get_price, PRICE_SCHEMA)
    agent.register(add, ADD_SCHEMA)

    answer = agent.run("What is the total price of one widget and one gadget?")
    print("\nFINAL:", answer)
    # Expect the agent to call get_price twice, then add -> 65.
