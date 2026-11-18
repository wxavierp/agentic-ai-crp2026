"""
11 - The same desk, declared instead of wired.

In LangGraph you drew the arrows yourself: this node, then that node, and here is the state they share.
CrewAI asks you for something different. You describe WHO is on the team - a role, a goal, a bit of
character - and WHAT each job is, and the framework arranges the work.

Same two agents as Saturday. Same hand-off. A completely different way of saying it.
Watch for one thing in particular: where the hand-off went.

Run:  python 11_crew.py          (needs OPENAI_API_KEY in your .env · pip install crewai)
"""
import os, sys, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from utils.kb_search import KnowledgeBase
from utils.crew_kit import Agent, Task, Crew, Process, USING

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))
kb = KnowledgeBase(chunks)


# ---- The Researcher (ready for you) ------------------------------------------------------------
# An agent is three sentences: who you are, what you are for, and why you are good at it.
researcher = Agent(
    role="Researcher",
    goal="Turn search results into short, honest notes a colleague can write a reply from",
    backstory="You have worked the Lumo support desk for years. You write one fact per line and you put "
              "the [id] of the result at the end of every line. If nothing in the results helps, you say "
              "exactly NOTHING FOUND rather than guessing.",
)


# ---- TODO 1: the Writer -------------------------------------------------------------------------
# TODO 1 - give the Writer a goal and a backstory. The backstory is not decoration: it is where you put
#          the rules. This one must use ONLY the Researcher's notes, cite every fact as [id], and say
#          "I don't know" when the notes say NOTHING FOUND.
# HINT:  goal="Write the reply the customer actually receives",
#        backstory="You write for customers, not for engineers. You cannot search: you only have the "
#                  "Researcher's notes. You use nothing else. After every fact you put its id in square "
#                  "brackets, like [err-4210]. If the notes say NOTHING FOUND you reply exactly: I don't know. "
#                  "Two sentences, friendly and plain."
writer = Agent(
    role="Writer",
    goal="",                                            # <- replace this line
    backstory="",                                       # <- and this one
)


# ---- The research job (ready for you) ----------------------------------------------------------
# {question} and {results} are filled in by kickoff(inputs=...).
research_task = Task(
    description="A customer asked: {question}\n\nThese are the search results:\n{results}",
    expected_output="One fact per line. Every line ends with the [id] it came from. "
                    "If no result helps, the single line: NOTHING FOUND",
    agent=researcher,
)


# ---- TODO 2 and TODO 3: the writing job --------------------------------------------------------
# TODO 2 - expected_output is not a comment. CrewAI sends it to the model as the definition of done,
#          and it is what you will argue about when the output is nearly right. Describe the reply you want.
# HINT:  expected_output="Two friendly sentences to the customer, with the [id] after every fact. "
#                        "If the notes say NOTHING FOUND: exactly  I don't know."
#
# TODO 3 - THE HAND-OFF. On Saturday you wrote the hand-off message by hand. In CrewAI it is one argument:
#          context says which finished jobs this job may see. With an empty context the Writer gets the
#          question and NOTHING ELSE - no notes, no search, nothing to stand on.
# HINT:  context=[research_task]
write_task = Task(
    description="Write the reply to the customer. Their question was: {question}",
    expected_output="an answer",                        # <- replace this line
    agent=writer,
    context=[],                                         # <- and this one
)


# ---- The crew (ready for you) ------------------------------------------------------------------
crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task],
            process=Process.sequential, verbose=False)


def ask(question):
    results = "\n".join("[%s] %s" % (i, t) for i, t in kb.search(question))
    out = crew.kickoff(inputs={"question": question, "results": results})
    notes = out.tasks_output[0].raw
    reply = out.tasks_output[-1].raw
    return notes, reply


# ---- Run it ------------------------------------------------------------------------------------
def check(reply, notes):
    """The same check as 06_two_agents.py: the reply may only cite ids that are in the notes."""
    if notes.strip().upper().startswith("NOTHING FOUND"):
        return "don't know" in reply.lower().replace("’", "'")
    cited = re.findall(r"\[([^\]]+)\]", reply)
    return bool(cited) and all(c in notes for c in cited)


TESTS = [
    "How long is the warranty on the Falcon S2 Pro, and can I return it?",
    "The display says E-4210. What should I do?",
    "Do you sell the Pixel 9 phone?",
]

print("Crew engine:", USING)
print()
good = 0
for question in TESTS:
    notes, reply = ask(question)
    ok = check(reply, notes)
    good += ok
    print("Q:", question)
    print("   notes :", notes.replace("\n", "\n           "))
    print("   reply :", reply.replace("\n", " "))
    print("   %s" % ("GOOD: the reply stands on the notes" if ok else "BAD: the reply is not backed by the notes"))
    print()
print("RESULT CHECK: %d of %d replies are backed by the hand-off." % (good, len(TESTS)))
if not write_task.context:
    print("   TODO 3 is not done yet: context is empty, so the Writer never sees the notes.")


# ---- The app (ready for you: nothing to fill in here) ------------------------------------------
import gradio as gr


def run_crew(question):
    if not question.strip():
        return "", "", ""
    notes, reply = ask(question)
    return notes, reply, ("GOOD: the reply stands on the notes" if check(reply, notes) else "BAD: not backed by the notes")


with gr.Blocks(title="The crew") as app:
    gr.Markdown("## Researcher and Writer, as a crew\nThe same two agents as Saturday - described as roles instead of wired as a graph.")
    box = gr.Textbox(label="Customer question", placeholder="for example: The display says E-4210")
    notes_box = gr.Textbox(label="The Researcher's notes (task 1 output)", lines=5)
    reply_box = gr.Textbox(label="The Writer's reply (task 2 output)", lines=3)
    verdict_box = gr.Textbox(label="Check")
    box.submit(run_crew, box, [notes_box, reply_box, verdict_box])
    gr.Button("Ask the crew", variant="primary").click(run_crew, box, [notes_box, reply_box, verdict_box])
    gr.Examples(TESTS, inputs=box)

app.launch(inbrowser=True)
