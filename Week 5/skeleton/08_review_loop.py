"""
08 - A review loop with a stop rule.

The Writer drafts a reply, a Reviewer checks it. If the Reviewer finds problems, the Writer tries again with the
Reviewer's complaints. That is a loop - and a loop with no stop rule can run for ever, and cost real money.
You write the stop rule, and the message that carries the complaints back to the Writer.

Run:  python 08_review_loop.py          (needs OPENAI_API_KEY in your .env)
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
MAX_ROUNDS = 3                                       # the most drafts we will ever write for one question


# ---- The agents (ready for you) ----------------------------------------------------------------
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


def first_message(question, notes):
    return "Customer question: %s\n\nResearcher's notes:\n%s" % (question, notes)


def reviewer(draft, notes, picky):
    """The Reviewer: returns a list of problems (an empty list = approved). Ready-made, no model needed."""
    problems = []
    cited = re.findall(r"\[([^\]]+)\]", draft)
    if notes.strip().startswith("NOTHING FOUND"):
        if "don't know" not in draft.lower().replace("’", "'"):
            problems.append("The notes say NOTHING FOUND, so the reply must say: I don't know.")
    else:
        if not cited:
            problems.append("No source is cited. Put the [id] after every fact.")
        for c in cited:
            if c not in notes:
                problems.append("The reply cites [%s], which is not in the notes." % c)
    if picky:                                         # a reviewer that ALWAYS finds something more to improve
        problems.append("Make it a little shorter and friendlier.")
    return problems


# ---- TODO 2: the message for a second try ------------------------------------------------------
def retry_message(question, notes, draft, problems):
    """What the Writer receives when the Reviewer sent the draft back."""
    # TODO 2 - start from first_message(...), then add the last draft and the Reviewer's problems, and ask for a new reply.
    # HINT:  first_message(question, notes) + "\n\nYour last draft:\n" + draft
    #        + "\n\nThe reviewer found these problems:\n- " + "\n- ".join(problems) + "\n\nWrite the reply again and fix them."
    return first_message(question, notes)


# ---- TODO 1: the stop rule ---------------------------------------------------------------------
def after_review(state):
    """Called after every review. Return "done" to stop, or "write" to send the draft back to the Writer."""
    # TODO 1 - stop when the Reviewer approved, OR when we have used MAX_ROUNDS rounds. Otherwise try again.
    # HINT:  if state["approved"] or state["rounds"] >= MAX_ROUNDS:
    #            return "done"
    #        return "write"
    return "done"


# ---- The graph (ready for you) -----------------------------------------------------------------
class State(TypedDict, total=False):
    question: str
    picky: bool
    notes: str
    draft: str
    problems: list
    approved: bool
    rounds: int
    history: list                                     # one (draft, problems) pair per round


def research_node(state):
    results = "\n".join("[%s] %s" % (i, t) for i, t in kb.search(state["question"]))
    notes = ask_model(RESEARCHER_RULES, "Question: %s\n\nSearch results:\n%s" % (state["question"], results))
    return {"notes": notes, "rounds": 0, "history": [], "problems": [], "approved": False}


def write_node(state):
    if state["problems"]:
        message = retry_message(state["question"], state["notes"], state["draft"], state["problems"])
    else:
        message = first_message(state["question"], state["notes"])
    return {"draft": ask_model(WRITER_RULES, message)}


def review_node(state):
    problems = reviewer(state["draft"], state["notes"], state["picky"])
    return {"problems": problems, "approved": not problems, "rounds": state["rounds"] + 1,
            "history": state["history"] + [(state["draft"], problems)]}


graph = StateGraph(State)
graph.add_node("research", research_node)
graph.add_node("write", write_node)
graph.add_node("review", review_node)
graph.set_entry_point("research")
graph.add_edge("research", "write")
graph.add_edge("write", "review")
graph.add_conditional_edges("review", after_review, {"write": "write", "done": END})
workflow = graph.compile()


def run(question, picky=False):
    return workflow.invoke({"question": question, "picky": picky})


def why_stopped(final):
    return "approved" if final["approved"] else "hit the limit of %d rounds - NOT approved" % MAX_ROUNDS


# ---- Run it ------------------------------------------------------------------------------------
print("Graph engine:", USING)
print()
print("A) A normal reviewer")
EASY = ["How long is the warranty on the Falcon S2 Pro, and can I return it?", "Do you sell the Pixel 9 phone?"]
approved = 0
for question in EASY:
    final = run(question)
    approved += final["approved"] and final["rounds"] <= MAX_ROUNDS
    print("  Q:", question)
    for n, (draft, problems) in enumerate(final["history"], 1):
        print("   round %d: %s" % (n, draft))
        print("            problems: %s" % (problems or "none"))
    print("   stopped: %s" % why_stopped(final))
    print()

print("B) A reviewer that is never satisfied")
picky_final = run(EASY[0], picky=True)
for n, (draft, problems) in enumerate(picky_final["history"], 1):
    print("   round %d: %s" % (n, draft))
    print("            problems: %s" % problems)
print("   stopped: %s" % why_stopped(picky_final))
print()
print("RESULT CHECK 1: %d of %d normal questions were approved." % (approved, len(EASY)))
print("RESULT CHECK 2: the never-satisfied reviewer was stopped after exactly %d rounds: %s"
      % (MAX_ROUNDS, "YES" if picky_final["rounds"] == MAX_ROUNDS and not picky_final["approved"] else "NO (rounds = %d)" % picky_final["rounds"]))


# ---- The app (ready for you: nothing to fill in here) ------------------------------------------
import gradio as gr


def run_loop(question, picky):
    if not question.strip():
        return "", "", ""
    final = run(question, picky)
    rounds = "\n".join("round %d: %s\n         problems: %s" % (n, d, p or "none") for n, (d, p) in enumerate(final["history"], 1))
    return rounds, final["draft"], why_stopped(final)


with gr.Blocks(title="Review loop") as app:
    gr.Markdown("## Writer and Reviewer\nAsk a question. Tick the box to use a reviewer that is never satisfied, and watch the stop rule end the loop.")
    box = gr.Textbox(label="Customer question", placeholder="for example: The display says E-4210")
    picky_box = gr.Checkbox(label="Reviewer is never satisfied")
    rounds_box = gr.Textbox(label="Every round", lines=8)
    final_box = gr.Textbox(label="Last draft", lines=3)
    stop_box = gr.Textbox(label="Why it stopped")
    box.submit(run_loop, [box, picky_box], [rounds_box, final_box, stop_box])
    gr.Button("Run the loop", variant="primary").click(run_loop, [box, picky_box], [rounds_box, final_box, stop_box])
    gr.Examples([[q, False] for q in EASY] + [[EASY[0], True]], inputs=[box, picky_box])

app.launch(inbrowser=True)
