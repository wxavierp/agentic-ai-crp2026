"""
01 · Build a ReAct agent — reason + act, interleaved.  (NEW · the Day-1 core build)

ReAct is the Week-1 loop with its REASONING brought into the open. At each step
the agent writes a THOUGHT, takes an ACTION (a native tool call), reads an
OBSERVATION, and repeats until it can give an ANSWER. Every step goes into a
TRACE you can inspect.

This is the Week-2 ToolAgent PLUS a reasoning prompt and a self.trace log.
You'll finish the loop inside ReActAgent.run().

-------------------------------------------------------------------
YOUR TASKS  (all inside ReActAgent.run())
  TODO 1 · ask the model for the next step:  self.client.chat(messages, tools=self.schemas)
           the assistant's text is this step's THOUGHT.
  TODO 2 · if the reply has NO tool calls, it's the final ANSWER — log the thought
           (if any) and return result.text.
  TODO 3 · otherwise append result.raw_message, then for each call: run the tool with
           self._run_tool(call), append a dict to self.trace
           {"thought","action","args","observation"}, and append a "tool" message.
-------------------------------------------------------------------
Run it:  python skeleton/01_react_agent.py
Stuck?   trainer/01_react_agent.py has the full version.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.llm_client import LLMClient

MAX_STEPS = 8

REACT_SYSTEM = (
    "You are a reasoning agent that solves tasks step by step.\n"
    "Think out loud: before each tool call, briefly state your reasoning in one sentence.\n"
    "Use the tools one at a time. When you have enough information, give the final answer "
    "in plain text with no tool call."
)


class ReActAgent:
    def __init__(self, system=REACT_SYSTEM):
        self.client = LLMClient()
        self.schemas = []
        self.functions = {}
        self.system = system
        self.trace = []     # list of {"thought","action","args","observation"}

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
        messages = [{"role": "system", "content": self.system},
                    {"role": "user", "content": goal}]

        for step in range(1, MAX_STEPS + 1):
            # TODO 1: ask the model for its next step (pass tools=self.schemas).
            result = None  # replace this
            thought = (result.text or "").strip() if result else ""

            # TODO 2: if not result.wants_tools: log the thought and return result.text

            # TODO 3: append result.raw_message, then for each call: run the tool,
            #         append to self.trace, and append a {"role":"tool", ...} message.
            pass

        return "Stopped: reached the step limit without a final answer."

    def print_trace(self):
        print("\n--- REASONING TRACE ---")
        for i, s in enumerate(self.trace, 1):
            if s["thought"]:
                print(f"[{i}] THOUGHT: {s['thought']}")
            if s["action"]:
                print(f"[{i}] ACTION: {s['action']}({s['args']})")
                print(f"[{i}] OBSERVATION: {s['observation']}")
        print("--- END TRACE ---")


# ---- deterministic, offline demo tools (given) ----
FAKE_WEATHER = {"dubai": 38, "london": 14, "tokyo": 22, "mumbai": 33}

def get_temperature(city: str):
    t = FAKE_WEATHER.get(city.strip().lower())
    return f"{t}°C" if t is not None else f"error: no reading for '{city}'"

TEMP_SCHEMA = {
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
}


if __name__ == "__main__":
    agent = ReActAgent()
    agent.register(get_temperature, TEMP_SCHEMA)

    answer = agent.run("Which is hotter right now, Dubai or London, and by how much?")
    print("\nFINAL:", answer)
    agent.print_trace()
    # Expect: a Thought, two get_temperature calls (Dubai, London), then the answer.
