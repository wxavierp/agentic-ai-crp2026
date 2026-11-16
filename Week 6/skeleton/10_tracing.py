"""
10 - Turn on the lights: tracing the desk with LangSmith.

Your desk now has four nodes and makes several model calls per question. When an answer is wrong or a run
is slow, the terminal tells you almost nothing: you see what came out, not what happened inside.

A TRACE is the record of one run: every step, in order, with what went IN, what came OUT, how long it took
and how many tokens it cost. LangSmith collects traces and draws them as a tree you can click through.

Today the desk has something wrong with it. You are not going to find it by reading the code.
You are going to turn on tracing, look at the run, and let the trace tell you.

Before you run this: put LANGSMITH_API_KEY and LANGSMITH_TRACING=true in your .env (see README, Set up).

Run:  python 10_tracing.py          (needs OPENAI_API_KEY and LANGSMITH_API_KEY in your .env)
"""
import os, sys, json, time
from typing import TypedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from utils.llm_client import LLMClient
from utils.kb_search import KnowledgeBase
from utils.graph_kit import StateGraph, END, USING
from langsmith import traceable                          # the decorator that makes a function a step in the trace

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))
kb = KnowledgeBase(chunks)
client = LLMClient()

CALLS = {"model": 0, "search": 0}                         # a local count, so you can check the trace against it


# ---- TODO 1: make the two helpers show up in the trace ------------------------------------------
# LangGraph already reports each NODE. These two helpers live inside the nodes, so without a decorator
# they are invisible: you would see "research took 6 seconds" and not know what it spent them on.
#
# TODO 1 - put a @traceable decorator on BOTH functions below, and give each one a name.
# HINT:  @traceable(name="ask_model")        above def ask_model
#        @traceable(name="search_kb")        above def search_kb
# (no decorator yet - add it here)
def ask_model(rules, message):
    CALLS["model"] += 1
    return client.get_completion(message, system_message=rules, temperature=0)


# (no decorator yet - add it here)
def search_kb(question):
    CALLS["search"] += 1
    return kb.search(question)


# ---- The desk (ready for you) -------------------------------------------------------------------
RESEARCHER_RULES = """You are the Researcher of the Lumo support desk.
You get a customer question and search results. Write short notes for a colleague: one fact per line, each line
ending with the [id] of the result it came from. If no result helps, write exactly: NOTHING FOUND"""

WRITER_RULES = """You are the Writer of the Lumo support desk.
Use ONLY the Researcher's notes. After every fact, cite its id in square brackets, like [err-4210].
If the notes say NOTHING FOUND, reply exactly: I don't know. Two sentences, friendly and plain."""


# ---- TODO 3: the thing the trace will show you --------------------------------------------------
# The Researcher does not search once. It searches once for the question, and once for every rewrite below,
# then throws the extra results into the same pile. Somebody added this "to find more", and nobody measured it.
#
# Do TODO 1 and TODO 2 first, run it, open the trace, and count the search_kb steps under "research".
# Then come back here.
#
# TODO 3 - make the Researcher search ONCE per question.
# HINT:  REWRITES = []
REWRITES = ["in other words: %s", "customer problem: %s", "help with %s"]     # <- replace this line


def research_node(state):
    question = state["question"]
    found = list(search_kb(question))
    for pattern in REWRITES:
        found += list(search_kb(pattern % question))
    seen, lines = set(), []
    for chunk_id, text in found:
        if chunk_id not in seen:
            seen.add(chunk_id)
            lines.append("[%s] %s" % (chunk_id, text))
    notes = ask_model(RESEARCHER_RULES, "Question: %s\n\nSearch results:\n%s" % (question, "\n".join(lines)))
    return {"notes": notes, "path": state["path"] + ["research"]}


def write_node(state):
    reply = ask_model(WRITER_RULES, "Customer question: %s\n\nResearcher's notes:\n%s" % (state["question"], state["notes"]))
    return {"reply": reply, "path": state["path"] + ["write"]}


class State(TypedDict, total=False):
    question: str
    notes: str
    reply: str
    path: list


graph = StateGraph(State)
graph.add_node("research", research_node)
graph.add_node("write", write_node)
graph.set_entry_point("research")
graph.add_edge("research", "write")
graph.add_edge("write", END)
workflow = graph.compile()


# ---- TODO 2: name your run so you can find it ----------------------------------------------------
# Your project will fill up with runs that are all called "LangGraph". A run name, a tag and a little
# metadata are what turn a pile of runs into something you can search.
#
# TODO 2 - build the config so every run is called "lumo-desk", is tagged "session-17",
#          and carries your own name in the metadata.
# HINT:  return {"run_name": "lumo-desk",
#                "tags": ["session-17"],
#                "metadata": {"student": YOUR_NAME, "rewrites": len(REWRITES)}}
YOUR_NAME = "put your name here"


def trace_config():
    return {}                                           # <- replace this line


def run(question):
    return workflow.invoke({"question": question, "path": []}, config=trace_config())


# ---- Run it --------------------------------------------------------------------------------------
TESTS = [
    "How long is the warranty on the Falcon S2 Pro, and can I return it?",
    "The display says E-4210. What should I do?",
    "Do you sell the Pixel 9 phone?",
]

tracing = os.getenv("LANGSMITH_TRACING", "").lower() == "true"
print("Graph engine :", USING)
print("Tracing      :", "ON - this run will appear in LangSmith" if tracing else
      "OFF - set LANGSMITH_TRACING=true and LANGSMITH_API_KEY in your .env, or you will see nothing in LangSmith")
cfg = trace_config()
print("Run config   :", cfg if cfg else "{}  (TODO 2 is not done yet: your runs will all be called LangGraph)")
print()

started = time.time()
for question in TESTS:
    CALLS["model"] = CALLS["search"] = 0
    t0 = time.time()
    final = run(question)
    print("Q:", question)
    print("   reply            :", final["reply"])
    print("   model calls      :", CALLS["model"])
    print("   searches         :", CALLS["search"])
    print("   seconds          : %.1f" % (time.time() - t0))
    print()

print("RESULT CHECK 1: searches per question = %d  (1 is right; 4 means TODO 3 is not done yet)" % CALLS["search"])
print("RESULT CHECK 2: model calls per question = %d  (2 is right: the Researcher and the Writer)" % CALLS["model"])
print("RESULT CHECK 3: all three questions took %.1f seconds in total." % (time.time() - started))
print()
print("Now open https://smith.langchain.com and find your run. Write down the three numbers above,")
print("and the same three as the trace reports them. They should agree.")


# ---- The app (ready for you: nothing to fill in here) --------------------------------------------
import gradio as gr


def run_traced(question):
    if not question.strip():
        return "", "", ""
    CALLS["model"] = CALLS["search"] = 0
    t0 = time.time()
    final = run(question)
    return final["reply"], final["notes"], "model calls: %d   searches: %d   seconds: %.1f" % (
        CALLS["model"], CALLS["search"], time.time() - t0)


with gr.Blocks(title="Traced desk") as app:
    gr.Markdown("## The desk, with the lights on\nEvery question you ask here appears in LangSmith as a run called `lumo-desk`.")
    box = gr.Textbox(label="Customer question", placeholder="for example: The display says E-4210")
    reply_box = gr.Textbox(label="Reply", lines=3)
    notes_box = gr.Textbox(label="The Researcher's notes", lines=5)
    cost_box = gr.Textbox(label="What this run cost")
    box.submit(run_traced, box, [reply_box, notes_box, cost_box])
    gr.Button("Ask the desk", variant="primary").click(run_traced, box, [reply_box, notes_box, cost_box])
    gr.Examples(TESTS, inputs=box)

app.launch(inbrowser=True)
