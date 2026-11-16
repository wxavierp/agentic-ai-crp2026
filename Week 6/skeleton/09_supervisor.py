"""
09 - The supervisor: a graph that chooses who works next.

In Session 16 your graph always ran the same way: research -> write. A real support desk is not like that.
"How long is the warranty?", "The display says E-4210" and "Do you sell the Pixel 9?" should go to three
different places - and the third one should not be answered by a robot at all.

So we put one node in FRONT of the specialists: the SUPERVISOR. It reads the question and names one
specialist. A conditional edge then sends the state to that specialist, and to nobody else.

What is new today: a conditional edge that picks between SEVERAL nodes by name, and a safe default
for the moment the model answers something you did not plan for.

Run:  python 09_supervisor.py          (needs OPENAI_API_KEY in your .env)
"""
import os, sys, json
from typing import TypedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from utils.llm_client import LLMClient
from utils.kb_search import KnowledgeBase
from utils.graph_kit import StateGraph, END, USING

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))
kb = KnowledgeBase(chunks)
client = LLMClient()

SPECIALISTS = ["warranty", "technical", "human"]        # the only three answers the supervisor may give


def ask_model(rules, message):
    return client.get_completion(message, system_message=rules, temperature=0)


# ---- The supervisor's rules (ready for you) ----------------------------------------------------
SUPERVISOR_RULES = """You are the supervisor of the Lumo support desk. You never answer the customer yourself.
You read the question and name the ONE specialist who should handle it.

warranty   - warranty cover, guarantees, returns, refunds, how long something is covered
technical  - error codes, a device not working as it should, charging, how to use it
human      - everything else: buying advice, products we may not sell, complaints, angry customers

Answer with exactly one word: warranty, technical or human. No punctuation, no explanation."""


# ---- TODO 1: the supervisor ----------------------------------------------------------------------
def choose_specialist(question):
    """Ask the model which specialist should take this question. Returns one word."""
    # TODO 1 - ask the model with SUPERVISOR_RULES, and return its answer in lower case with no spaces around it.
    # HINT:  answer = ask_model(SUPERVISOR_RULES, question)
    #        return answer.strip().lower()
    return ""                                           # <- replace this line


# ---- TODO 2: the safe default ----------------------------------------------------------------------
def route(state):
    """Called after the supervisor node. Returns the NAME of the node that runs next."""
    # TODO 2 - return the specialist the supervisor chose, but ONLY if it is one of SPECIALISTS.
    #          Anything else - an empty answer, a whole sentence, a word you did not plan for -
    #          must go to "human". A graph with no safe default crashes on the first surprise.
    # HINT:  if state["specialist"] in SPECIALISTS:
    #            return state["specialist"]
    #        return "human"
    return "human"                                      # <- replace this line


# ---- The specialists (ready for you) -----------------------------------------------------------
WARRANTY_RULES = """You are the warranty specialist of the Lumo support desk.
Answer only from the search results you are given. After every fact, cite its id in square brackets, like [orion-x2-warranty].
If the results do not answer the question, reply exactly: I don't know.
Two sentences, friendly and plain."""

TECHNICAL_RULES = """You are the technical specialist of the Lumo support desk.
Answer only from the search results you are given. After every fact, cite its id in square brackets, like [err-4210].
If the results do not answer the question, reply exactly: I don't know.
Two sentences, friendly and plain."""


def answer_from_kb(question, rules):
    results = "\n".join("[%s] %s" % (i, t) for i, t in kb.search(question))
    return ask_model(rules, "Customer question: %s\n\nSearch results:\n%s" % (question, results))


def supervise_node(state):
    return {"specialist": choose_specialist(state["question"]), "path": state["path"] + ["supervise"]}


def warranty_node(state):
    return {"answer": answer_from_kb(state["question"], WARRANTY_RULES), "path": state["path"] + ["warranty"]}


def technical_node(state):
    return {"answer": answer_from_kb(state["question"], TECHNICAL_RULES), "path": state["path"] + ["technical"]}


def human_node(state):
    """No model, no knowledge base: this one writes a note for a person and stops."""
    return {"answer": "Passing this to a colleague. Note for them: " + state["question"],
            "path": state["path"] + ["human"]}


class State(TypedDict, total=False):
    question: str
    specialist: str                                     # what the supervisor said
    answer: str
    path: list                                          # which nodes ran, in order


# ---- TODO 3: the map from an answer to a node --------------------------------------------------
# A conditional edge needs to know, for every value route() can return, which node to run.
# TODO 3 - send each specialist to its own node. Right now every answer lands on the human,
#          so the two specialists never run.
# HINT:  ROUTES = {"warranty": "warranty", "technical": "technical", "human": "human"}
ROUTES = {"warranty": "human", "technical": "human", "human": "human"}     # <- replace this line


# ---- The graph (ready for you: you drew one of these in Session 16) ----------------------------
graph = StateGraph(State)
graph.add_node("supervise", supervise_node)
graph.add_node("warranty", warranty_node)
graph.add_node("technical", technical_node)
graph.add_node("human", human_node)
graph.set_entry_point("supervise")
graph.add_conditional_edges("supervise", route, ROUTES)
for name in SPECIALISTS:
    graph.add_edge(name, END)
workflow = graph.compile()


# ---- Run it ------------------------------------------------------------------------------------
TESTS = [
    ("How long is the warranty on the Falcon S2 Pro, and can I return it?", "warranty"),
    ("I want a refund for the Vega M5 I bought last week.",                 "warranty"),
    ("The display says E-4210. What should I do?",                          "technical"),
    ("My Orion X2 only plays for four hours after a full charge.",          "technical"),
    ("Do you sell the Pixel 9 phone?",                                      "human"),
    ("This is the third time your delivery is late. I want a manager.",     "human"),
]

print("Graph engine:", USING)
print()
right = 0
one_path_only = True
said = []
for question, expected in TESTS:
    final = workflow.invoke({"question": question, "path": []})
    went = final["path"][-1]
    said.append(final["specialist"])
    ok = went == expected
    right += ok
    if len(final["path"]) != 2:                          # supervise + exactly ONE specialist
        one_path_only = False
    print("Q:", question)
    print("   supervisor said : %r" % final["specialist"])
    print("   path            : %s" % " -> ".join(final["path"]))
    print("   expected        : %s   %s" % (expected, "OK" if ok else "WRONG"))
    print("   answer          : %s" % final["answer"])
    print()

print("RESULT CHECK 1: %d of %d questions reached the right specialist." % (right, len(TESTS)))
print("RESULT CHECK 2: every run used exactly one specialist: %s" % ("YES" if one_path_only else "NO"))
if not any(said):
    print("   TODO 1 is not done yet: the supervisor is saying nothing, so every question falls to the human.")
elif right < len(TESTS):
    print("   Look at the path lines above: which questions went to the wrong place, and what did the supervisor say for them?")


# ---- The app (ready for you: nothing to fill in here) ------------------------------------------
import gradio as gr


def run_desk(question):
    if not question.strip():
        return "", "", ""
    final = workflow.invoke({"question": question, "path": []})
    return final["specialist"], " -> ".join(final["path"]), final["answer"]


with gr.Blocks(title="Supervisor desk") as app:
    gr.Markdown("## The supervisor desk\nOne question in. The supervisor names a specialist; the conditional edge sends it there, and nowhere else.")
    box = gr.Textbox(label="Customer question", placeholder="for example: The display says E-4210")
    said_box = gr.Textbox(label="What the supervisor said")
    path_box = gr.Textbox(label="Path the run took")
    answer_box = gr.Textbox(label="The specialist's answer", lines=3)
    box.submit(run_desk, box, [said_box, path_box, answer_box])
    gr.Button("Send to the desk", variant="primary").click(run_desk, box, [said_box, path_box, answer_box])
    gr.Examples([q for q, _ in TESTS], inputs=box)

app.launch(inbrowser=True)
