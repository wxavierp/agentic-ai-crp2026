"""
05 · ADVANCED / OPTIONAL — the same ReAct loop, as a LangGraph graph.  (skeleton)

In Lab 1 you hand-built reason -> act -> (loop) -> answer. Frameworks like
LangGraph express that as a GRAPH: nodes do work, edges decide what runs next,
and a shared STATE flows between them. This file builds the exact same ReAct
agent as a tiny StateGraph so you can see the mapping — nothing here is new
behaviour, only a new way to wire it.

This is optional and needs one extra install:
    pip install langgraph
Then:
    python skeleton/05_langgraph_react.py

If langgraph isn't installed, the file prints how to get it and exits cleanly.
"""

import sys, os, json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.llm_client import LLMClient

try:
    from langgraph.graph import StateGraph, END
    from typing import TypedDict, List
except ImportError:
    print("This optional demo needs LangGraph.  Install it with:\n    pip install langgraph")
    sys.exit(0)


FAKE_WEATHER = {"dubai": 38, "london": 14, "tokyo": 22}

def get_temperature(city: str):
    t = FAKE_WEATHER.get(city.strip().lower())
    return f"{t}°C" if t is not None else f"error: no reading for '{city}'"

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_temperature",
        "description": "Get the current temperature in Celsius for a city.",
        "parameters": {"type": "object",
                       "properties": {"city": {"type": "string"}},
                       "required": ["city"]},
    },
}]

client = LLMClient()


class State(TypedDict):
    messages: List[dict]
    answer: str


def reason(state: State):
    """The REASON node: ask the model for the next step."""
    result = client.chat(state["messages"], tools=TOOLS)
    state["messages"].append(result.raw_message)
    if not result.wants_tools:
        state["answer"] = result.text
    return state


def act(state: State):
    """The ACT node: run each requested tool and append the observations."""
    last = state["messages"][-1]
    # TODO A: for each tool_call on `last`, parse its JSON args, run get_temperature,
    #         and append a {"role":"tool","tool_call_id":...,"content":...} message.
    return state


def should_continue(state: State):
    """The EDGE: stop if we have an answer, else loop back to reason."""
    # TODO B: return END when state has an answer, otherwise "act".
    return END


def build_graph():
    g = StateGraph(State)
    g.add_node("reason", reason)
    g.add_node("act", act)
    g.set_entry_point("reason")
    g.add_conditional_edges("reason", should_continue, {"act": "act", END: END})
    g.add_edge("act", "reason")
    return g.compile()


if __name__ == "__main__":
    graph = build_graph()
    init = {"messages": [{"role": "user",
             "content": "Which is hotter now, Dubai or London?"}], "answer": ""}
    final = graph.invoke(init)
    print("FINAL:", final["answer"])
    # Same reason/act/answer loop as Lab 1 — just wired as nodes and edges.
