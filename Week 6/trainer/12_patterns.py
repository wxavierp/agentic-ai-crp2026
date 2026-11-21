"""
12 - Three shapes of a team, and what each one costs.

So far every team you have built has been a LINE: one agent, then the next. That is one shape out of
several, and it is not always the right one.

Tonight's shape is FAN-OUT AND PICK. Three specialists answer the SAME question at the same time, and a
judge reads all three and picks one. You use it when you do not know in advance who is best placed to
answer - which, on a real desk, is most of the time.

The file runs the same work twice, as a line and as a fan-out, and prints what each shape cost you.
Then  --manager  runs it a third way: nobody is told who does what, and a manager decides at run time.

Run:  python 12_patterns.py            (needs OPENAI_API_KEY · pip install crewai)
      python 12_patterns.py --manager  (the third shape)
"""
import os, sys, json, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from utils.kb_search import KnowledgeBase
from utils.crew_kit import Agent, Task, Crew, Process, USING

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))
kb = KnowledgeBase(chunks)
SPECIALISTS = ["Warranty specialist", "Technical specialist", "Delivery specialist"]


# ---- The three specialists and the judge (ready for you) ---------------------------------------
def specialist(role, about):
    return Agent(role=role, goal="Answer the customer's question from the search results, or admit it is not yours",
                 backstory="You only know about %s. Use ONLY the search results you are given and put the [id] "
                           "after every fact. If the question is not about %s, or the results do not answer it, "
                           "reply exactly: NOT MINE." % (about, about))


warranty = specialist("Warranty specialist", "warranty cover, guarantees, returns and refunds")
technical = specialist("Technical specialist", "error codes, charging and how a device is used")
delivery = specialist("Delivery specialist", "shipping, delivery times and tracking")

judge = Agent(
    role="Judge",
    goal="Choose the one answer the customer should actually receive",
    backstory="You read what the specialists sent and pick ONE. An answer that says NOT MINE is never the "
              "winner. An answer with no [id] is never the winner. You do not rewrite the answer and you "
              "do not merge two answers: you pick one and pass it on.",
)


def three_tasks(async_on):
    """One task per specialist - the SAME question to all three."""
    return [Task(description="A customer asked: {question}\n\nSearch results:\n{results}",
                 expected_output="Either the answer with an [id] after every fact, or exactly: NOT MINE",
                 agent=a, async_execution=async_on) for a in (warranty, technical, delivery)]


# ---- TODO 1 and TODO 2: the fan-out ------------------------------------------------------------
# TODO 1 - make the three specialists work AT THE SAME TIME instead of one after another.
#          three_tasks(async_on) already passes it through; you choose what to pass.
# HINT:  fan = three_tasks(True)
#
# TODO 2 - the judge has to see all three answers. context is the list of finished jobs this job may read.
# HINT:  context=fan
fan = three_tasks(True)

judge_task = Task(
    description="The customer asked: {question}\nThree specialists have answered. Choose the one reply to send.",
    expected_output="Line 1: CHOSEN: <the exact role of the specialist you picked>\n"
                    "Then their answer, copied as it is, with the [id]s left in place.",
    agent=judge,
    context=fan,
)
# TODO 3 - look at expected_output above. Make the judge name the specialist it chose on the first line,
#          exactly as  CHOSEN: <role>  , then copy that specialist's answer underneath.
# HINT:  expected_output="Line 1: CHOSEN: <the exact role of the specialist you picked>\n"
#                        "Then their answer, copied as it is, with the [id]s left in place."


# ---- The two shapes (ready for you) ------------------------------------------------------------
MANAGER = "--manager" in sys.argv

manager = Agent(role="Desk manager", goal="Send each question to the right specialist",
                backstory="You never answer a customer. You read the question and name the one specialist "
                          "who should take it.")


def build(tasks, hierarchical=False):
    return Crew(agents=[warranty, technical, delivery, judge], tasks=tasks,
                process=Process.hierarchical if hierarchical else Process.sequential,
                manager_agent=manager if hierarchical else None, verbose=MANAGER)


def run(question, tasks, hierarchical=False):
    results = "\n".join("[%s] %s" % (i, t) for i, t in kb.search(question, k=5))
    t0 = time.time()
    out = build(tasks, hierarchical).kickoff(inputs={"question": question, "results": results})
    return out, time.time() - t0


def chosen(text):
    first = text.strip().split("\n")[0]
    for role in SPECIALISTS:
        if role.lower() in first.lower():
            return role
    return None


# ---- Run it ------------------------------------------------------------------------------------
TESTS = [
    ("The display says E-4210. What should I do?", "Technical specialist"),
    ("How long does delivery take for the Orion X2?", "Delivery specialist"),
]

print("Crew engine:", USING)
print("Fan-out is", "ON" if fan[0].async_execution else "OFF  (TODO 1 is not done yet)")
print()

if MANAGER:
    print("THIRD SHAPE: nobody is told who does what - the manager decides at run time.")
    for question, _ in TESTS:
        one = Task(description="A customer asked: {question}\n\nSearch results:\n{results}",
                   expected_output="The answer with an [id] after every fact.", agent=warranty)
        out, secs = run(question, [one], hierarchical=True)
        print("Q:", question)
        print("   answer  :", out.raw.replace("\n", " ")[:160])
        print("   seconds : %.1f" % secs)
        print()
    print("RESULT CHECK: who decided which specialist answered - you, or the manager?")
    sys.exit(0)

def same_work_as_a_line():
    """The identical four jobs, with the three specialists one after another instead of at once."""
    three = three_tasks(False)
    last = Task(description=judge_task.description, expected_output=judge_task.expected_output,
                agent=judge, context=three if judge_task.context else [])
    return three + [last]


named = 0
for question, expected in TESTS:
    _, line_secs = run(question, same_work_as_a_line())
    out, fan_secs = run(question, fan + [judge_task])
    pick = chosen(out.raw)
    ok = pick == expected
    named += ok
    print("Q:", question)
    print("   one after another : %.1f s" % line_secs)
    print("   all at once       : %.1f s" % fan_secs)
    print("   the judge chose   : %s   (expected %s)   %s" % (pick or "nobody - no CHOSEN: line", expected,
                                                              "OK" if ok else "WRONG"))
    print("   reply             :", out.raw.replace("\n", " ")[:160])
    print()

print("RESULT CHECK 1: the judge named the right specialist in %d of %d questions." % (named, len(TESTS)))
print("RESULT CHECK 2: fan-out is %s. Three specialists cost 3 model calls either way -" %
      ("ON" if fan[0].async_execution else "OFF"))
print("                running them at once buys you TIME, not money.")
print()
print("Now run:  python 12_patterns.py --manager")
