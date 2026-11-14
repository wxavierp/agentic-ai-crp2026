"""
07 - The same workflow as a graph.

In 06 you called the two agents one after the other, in plain Python. A graph says the same thing as a picture:
boxes (nodes) and arrows (edges). The state is one dictionary that every node reads and adds to.
Why bother? Because the next step (a review loop, in 08) is just one more arrow.

Run:  python 07_graph.py          (needs OPENAI_API_KEY in your .env; uses langgraph if it is installed)
"""
import os, sys, json, re
from typing import TypedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from utils.llm_client import LLMClient
from utils.kb_search import KnowledgeBase
from utils.graph_kit import StateGraph, END, USING

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))
kb = KnowledgeBase(chunks)
client = LLMClient()


# ---- The two agents from 06 (ready for you) ----------------------------------------------------
def ask_model(rules, message):
    return client.get_completion(message, system_message=rules, temperature=0)


RESEARCHER_RULES = """You are the Researcher of the Lumo support desk.
You get a customer question and search results. Write short notes for a colleague: one fact per line, each line ending with the [id] of the result it came from.
Write only facts that help to answer the question. If no result helps, write exactly: NOTHING FOUND"""

WRITER_RULES = """You are the Writer of the Lumo support desk.
You write the reply to the customer. You cannot search: you only have the Researcher's notes.
Use ONLY the notes. After every fact, cite its id in square brackets, like [err-4210].
If the notes say NOTHING FOUND, reply exactly: I don't know.
Keep the reply to two sentences, friendly and plain."""


def researcher(question):
    results = "\n".join("[%s] %s" % (i, t) for i, t in kb.search(question))
    return ask_model(RESEARCHER_RULES, "Question: %s\n\nSearch results:\n%s" % (question, results))


def writer(question, notes):
    return ask_model(WRITER_RULES, "Customer question: %s\n\nResearcher's notes:\n%s" % (question, notes))


# ---- The state: one dictionary that every node can read ----------------------------------------
class State(TypedDict, total=False):
    question: str
    notes: str
    reply: str
    path: list                                      # which nodes ran, in order


# ---- TODO 1: one node per agent ----------------------------------------------------------------
# A node is a function: it gets the state and returns ONLY the keys it changes.
def research_node(state):
    notes = researcher(state["question"])
    return {"notes": notes, "path": state["path"] + ["research"]}


def write_node(state):
    # TODO 1 - the same as research_node, for the Writer: call writer(...) with the question and the notes,
    #          and return the reply, and the path with "write" added.
    # HINT:  reply = writer(state["question"], state["notes"])
    #        return {"reply": reply, "path": state["path"] + ["write"]}
    return {"reply": "TODO 1 is not done yet", "path": state["path"] + ["write"]}


# ---- TODO 2: draw the graph --------------------------------------------------------------------
graph = StateGraph(State)
# TODO 2 - add the two nodes, say where to start, and join them:  research -> write -> END
# HINT:  graph.add_node("research", research_node)
#        graph.add_node("write", write_node)
#        graph.set_entry_point("research")
#        graph.add_edge("research", "write")
#        graph.add_edge("write", END)
workflow = None                                     # replace with:  graph.compile()  (after your lines above)

if workflow is None:
    sys.exit("TODO 2 is not done yet: add the nodes and edges, then  workflow = graph.compile()")


# ---- Run it ------------------------------------------------------------------------------------
def check(final):
    """The graph ran research then write, and the reply cites only ids from the notes (or says I don't know)."""
    if final["path"] != ["research", "write"]:
        return False
    if final["notes"].strip().startswith("NOTHING FOUND"):
        return "don't know" in final["reply"].lower().replace("’", "'")
    cited = re.findall(r"\[([^\]]+)\]", final["reply"])
    return bool(cited) and all(c in final["notes"] for c in cited)


TESTS = [
    "How long is the warranty on the Falcon S2 Pro, and can I return it?",
    "The display says E-4210. What should I do?",
    "Do you sell the Pixel 9 phone?",
]
print("Graph engine:", USING)
print()
good = 0
for question in TESTS:
    final = workflow.invoke({"question": question, "path": []})
    ok = check(final)
    good += ok
    print("Q:", question)
    print("   path  :", " -> ".join(final["path"]))
    print("   reply :", final["reply"])
    print("   %s" % ("GOOD" if ok else "BAD"))
    print()
print("RESULT CHECK: %d of %d runs went research -> write and ended with a backed reply." % (good, len(TESTS)))


# ---- The app (ready for you: nothing to fill in here) ------------------------------------------
import gradio as gr


def run_graph(question):
    if not question.strip():
        return "", "", ""
    final = workflow.invoke({"question": question, "path": []})
    return " -> ".join(final["path"]), final["notes"], final["reply"]


with gr.Blocks(title="Support graph") as app:
    gr.Markdown("## Support graph\nThe same two agents, now as a graph: research -> write.")
    box = gr.Textbox(label="Customer question", placeholder="for example: Do you sell the Pixel 9 phone?")
    path_box = gr.Textbox(label="Path the run took")
    notes_box = gr.Textbox(label="State: notes (from the research node)", lines=4)
    reply_box = gr.Textbox(label="State: reply (from the write node)", lines=3)
    box.submit(run_graph, box, [path_box, notes_box, reply_box])
    gr.Button("Run the graph", variant="primary").click(run_graph, box, [path_box, notes_box, reply_box])
    gr.Examples(TESTS, inputs=box)

app.launch(inbrowser=True)
