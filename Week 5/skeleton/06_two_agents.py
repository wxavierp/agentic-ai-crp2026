"""
06 - Two agents and a hand-off.

One agent finds the facts (the Researcher). A second agent writes the reply (the Writer).
The Writer cannot search: it sees ONLY the message the Researcher hands over.
So what goes into that message decides how good the reply can be.

Run:  python 06_two_agents.py          (needs OPENAI_API_KEY in your .env)
"""
import os, sys, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))          # Week 5/utils is shared
from utils.llm_client import LLMClient
from utils.kb_search import KnowledgeBase

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))
kb = KnowledgeBase(chunks)                          # the Day 14 search
client = LLMClient()                                # the chat model from your .env


def ask_model(rules, message):
    """One call to the chat model: the rules (system message) and the message. Returns the text."""
    return client.get_completion(message, system_message=rules, temperature=0)


# ---- Agent 1, the Researcher (ready for you) ---------------------------------------------------
RESEARCHER_RULES = """You are the Researcher of the Lumo support desk.
You get a customer question and search results. Write short notes for a colleague: one fact per line, each line ending with the [id] of the result it came from.
Write only facts that help to answer the question. If no result helps, write exactly: NOTHING FOUND"""


def researcher(question):
    found = kb.search(question)
    results = "\n".join("[%s] %s" % (chunk_id, text) for chunk_id, text in found)
    return ask_model(RESEARCHER_RULES, "Question: %s\n\nSearch results:\n%s" % (question, results))


# ---- TODO 1: the hand-off message --------------------------------------------------------------
def make_handoff(question, notes):
    """The message the Researcher hands to the Writer. The Writer sees nothing else."""
    # TODO 1 - put the customer's question and the Researcher's notes into one message.
    # HINT:  "Customer question: " + question + "\n\nResearcher's notes:\n" + notes
    return None


if make_handoff("a question", "some notes") is None:
    sys.exit("TODO 1 is not done yet: make_handoff() must return the message for the Writer (see the HINT).")


# ---- TODO 2: the Writer's rules ----------------------------------------------------------------
# TODO 2 - write the rules. The Writer cannot search, so it must work only from the notes.
# HINT:  four rules are enough:  (1) use ONLY the notes   (2) cite the [id] after every fact
#        (3) if the notes say NOTHING FOUND, reply exactly: I don't know.   (4) keep it to two sentences
WRITER_RULES = """You are the Writer of the Lumo support desk. You write the reply to the customer."""


def writer(handoff):
    return ask_model(WRITER_RULES, handoff)


# ---- Run it ------------------------------------------------------------------------------------
def check(reply, notes):
    """Did the hand-off work? The reply must cite only ids that are in the notes - or say I don't know when nothing was found."""
    if notes.strip().startswith("NOTHING FOUND"):
        return "don't know" in reply.lower().replace("’", "'")
    cited = re.findall(r"\[([^\]]+)\]", reply)
    return bool(cited) and all(c in notes for c in cited)


TESTS = [
    "How long is the warranty on the Falcon S2 Pro, and can I return it?",
    "The display says E-4210. What should I do?",
    "Do you sell the Pixel 9 phone?",
]
good = 0
for question in TESTS:
    notes = researcher(question)
    handoff = make_handoff(question, notes)
    reply = writer(handoff)
    ok = check(reply, notes)
    good += ok
    print("Q:", question)
    print("   notes :", notes.replace("\n", "\n           "))
    print("   reply :", reply)
    print("   %s" % ("GOOD: the reply stands on the notes" if ok else "BAD: the reply is not backed by the notes"))
    print()
print("RESULT CHECK: %d of %d replies are backed by the hand-off." % (good, len(TESTS)))
print("Try it: delete the notes from make_handoff and run again - what can the Writer still say?")


# ---- The app (ready for you: nothing to fill in here) ------------------------------------------
import gradio as gr


def run_desk(question):
    if not question.strip():
        return "", "", ""
    notes = researcher(question)
    handoff = make_handoff(question, notes)
    reply = writer(handoff)
    return handoff, reply, ("GOOD: the reply stands on the notes" if check(reply, notes) else "BAD: the reply is not backed by the notes")


with gr.Blocks(title="Two agents") as app:
    gr.Markdown("## Researcher and Writer\nAsk a question. The Researcher searches and hands over notes; the Writer answers from the notes only.")
    box = gr.Textbox(label="Customer question", placeholder="for example: The display says E-4210")
    handoff_box = gr.Textbox(label="The hand-off message (all the Writer sees)", lines=5)
    reply_box = gr.Textbox(label="The Writer's reply", lines=3)
    verdict_box = gr.Textbox(label="Check")
    box.submit(run_desk, box, [handoff_box, reply_box, verdict_box])
    gr.Button("Ask the desk", variant="primary").click(run_desk, box, [handoff_box, reply_box, verdict_box])
    gr.Examples(TESTS, inputs=box)

app.launch(inbrowser=True)                        # opens in your browser: http://127.0.0.1:7860
