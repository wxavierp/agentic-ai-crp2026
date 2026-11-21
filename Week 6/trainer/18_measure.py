"""
18 - Would you ship it?

You have a desk. Somebody is about to ask you whether it is good enough to put in front of customers,
and "it seemed fine when I tried it" is not an answer.

So: six golden tasks, three checks, one scorecard. The desk itself is ready-made below - a compact copy
of 17. Everything you write today is MEASUREMENT, because that is the skill nobody practises.

The three checks are not interchangeable. Routing right and being grounded and escalating correctly
fail in different ways, and a system can be excellent at one while being dangerous at another.

Run:  python 18_measure.py          (needs OPENAI_API_KEY; N8N_WEBHOOK_URL optional)
"""
import os, sys, json, re, time
from typing import TypedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from utils.llm_client import LLMClient
from utils.graph_kit import StateGraph, END
from utils.mcp_kit import McpServer
from utils.n8n_kit import post_to_n8n

client = LLMClient()
search_server = McpServer(os.path.join(HERE, "mcp_lumo_server.py"))
DESTINATIONS = ["warranty", "technical", "escalate"]

SUPERVISOR_RULES = """You are the supervisor of the Lumo support desk. You never answer the customer.
warranty   - warranty cover, guarantees, returns, refunds
technical  - error codes, charging, how a device is used
escalate   - damage, a complaint, something lost or late, or anything a human must act on
Answer with exactly one word: warranty, technical or escalate."""

ANSWER_RULES = """You are a specialist on the Lumo support desk.
Answer ONLY from the search results you are given, and put the [id] after every fact.
If the results do not answer it, reply exactly: I don't know. Two sentences."""


# ---- The desk (ready for you: this is 17, compressed) ------------------------------------------
class State(TypedDict, total=False):
    question: str
    order_id: str
    reply: str
    results: str
    escalated: bool
    path: list


def ask_model(rules, message):
    return client.get_completion(message, system_message=rules, temperature=0)


def supervise_node(state):
    said = ask_model(SUPERVISOR_RULES, state["question"]).strip().lower()
    return {"destination": said, "path": state["path"] + ["supervise"]}


def answer_node(name):
    def node(state):
        results = search_server.call("search_knowledge", question=state["question"])
        reply = ask_model(ANSWER_RULES, "Customer question: %s\n\nSearch results:\n%s"
                          % (state["question"], results))
        return {"reply": reply, "results": results, "escalated": False, "path": state["path"] + [name]}
    return node


def escalate_node(state):
    answer = post_to_n8n({"order_id": state.get("order_id") or "unknown",
                          "reason": "the desk could not answer this", "question": state["question"]})
    reply = ("I have passed this to a colleague (%s)." % answer.get("ticket")) if answer.get("ok") else \
            "I could not reach our support system just now, so nothing has been logged yet."
    return {"reply": reply, "results": "", "escalated": bool(answer.get("ok")),
            "path": state["path"] + ["escalate"]}


graph = StateGraph(State)
graph.add_node("supervise", supervise_node)
for name in ("warranty", "technical"):
    graph.add_node(name, answer_node(name))
graph.add_node("escalate", escalate_node)
graph.set_entry_point("supervise")
graph.add_conditional_edges("supervise", lambda s: s["destination"] if s["destination"] in DESTINATIONS else "escalate",
                            {d: d for d in DESTINATIONS})
for name in DESTINATIONS:
    graph.add_edge(name, END)
workflow = graph.compile()


# ---- The golden tasks (ready for you) ----------------------------------------------------------
# Six, on purpose: two that should be answered, two that should be escalated, one the desk CANNOT
# answer (and must admit), and one that looks like a product question but is really a complaint.
TASKS = [
    {"id": "G1", "question": "How long is the warranty on the Falcon S2 Pro?",
     "order_id": None, "route": "warranty", "must_cite": True, "must_escalate": False},
    {"id": "G2", "question": "The display says E-4210. What should I do?",
     "order_id": None, "route": "technical", "must_cite": True, "must_escalate": False},
    {"id": "G3", "question": "My Orion X2 from order LM-1003 arrived with a cracked case.",
     "order_id": "LM-1003", "route": "escalate", "must_cite": False, "must_escalate": True},
    {"id": "G4", "question": "Order LM-1004 is three weeks late and nobody has replied.",
     "order_id": "LM-1004", "route": "escalate", "must_cite": False, "must_escalate": True},
    {"id": "G5", "question": "What is the warranty on the Pixel 9 phone?",
     "order_id": None, "route": None, "must_cite": False, "must_escalate": False, "must_abstain": True},
    {"id": "G6", "question": "I have asked twice about the warranty on my Vega M5 and been ignored.",
     "order_id": None, "route": "escalate", "must_cite": False, "must_escalate": True},
]


# ---- TODO 1: did it go to the right place? -----------------------------------------------------
# TODO 1 - the last node the run visited is where it ended up. Compare it with the expected route.
#          A task with route None has no expected destination: it passes either way.
# HINT:  if task["route"] is None: return True
#        return result["path"][-1] == task["route"]
def routed_right(task, result):
    if task["route"] is None:
        return True
    return result["path"][-1] == task["route"]


# ---- TODO 2: is the answer standing on anything? -----------------------------------------------
# The hardest of the three, and the one people get wrong by making it too easy. An answer is GROUNDED
# when every [id] it cites actually appeared in the search results it was given. An answer that cites
# nothing is not grounded - unless it is an honest "I don't know", which is a correct answer.
#
# TODO 2 - return True when every cited id is in the results, or when the desk honestly abstained.
# HINT:  reply, results = result.get("reply", ""), result.get("results", "")
#        if "don't know" in reply.lower().replace("’", "'"): return True
#        cited = re.findall(r"\[([^\]]+)\]", reply)
#        return bool(cited) and all(c in results for c in cited)
def is_grounded(task, result):
    reply, results = result.get("reply", ""), result.get("results", "")
    if not results:                                     # it never searched - nothing to be wrong about
        return True
    if "don't know" in reply.lower().replace("’", "'"):
        return True
    cited = re.findall(r"\[([^\]]+)\]", reply)
    return bool(cited) and all(c in results for c in cited)


# ---- TODO 3: did it escalate exactly when it should? -------------------------------------------
# Both directions are failures, and they are not equally bad. Escalating when you did not need to wastes
# a person's time. NOT escalating when you should leaves an angry customer talking to a robot.
#
# TODO 3 - True when escalation happened if and only if the task says it should have.
# HINT:  return bool(result.get("escalated")) == bool(task["must_escalate"])
def escalated_right(task, result):
    return bool(result.get("escalated")) == bool(task["must_escalate"])


# ---- Run it ------------------------------------------------------------------------------------
rows, totals = [], {"routed": 0, "grounded": 0, "escalated": 0}
started = time.time()
for task in TASKS:
    t0 = time.time()
    result = workflow.invoke({"question": task["question"], "order_id": task["order_id"], "path": []})
    checks = {"routed": routed_right(task, result), "grounded": is_grounded(task, result),
              "escalated": escalated_right(task, result)}
    for k, v in checks.items():
        totals[k] += bool(v)
    rows.append((task["id"], result["path"][-1], checks, time.time() - t0,
                 (result.get("reply") or "").replace("\n", " ")[:60]))

print("%-4s %-10s %-7s %-9s %-10s %-6s %s" % ("id", "went to", "routed", "grounded", "escalated", "secs", "reply"))
print("-" * 110)
for tid, went, checks, secs, reply in rows:
    print("%-4s %-10s %-7s %-9s %-10s %-6.1f %s" % (
        tid, went, "PASS" if checks["routed"] else "FAIL", "PASS" if checks["grounded"] else "FAIL",
        "PASS" if checks["escalated"] else "FAIL", secs, reply))
print()
n = len(TASKS)
print("RESULT CHECK 1: routing      %d of %d" % (totals["routed"], n))
print("RESULT CHECK 2: grounded     %d of %d" % (totals["grounded"], n))
print("RESULT CHECK 3: escalation   %d of %d" % (totals["escalated"], n))
print("RESULT CHECK 4: %d golden tasks in %.1f seconds" % (n, time.time() - started))
print()
worst = min(totals, key=totals.get)
if min(totals.values()) == n:
    print("Would you ship it? Every check passes on six tasks. Six tasks is not many - say what you would add.")
else:
    print("Would you ship it? NO. The weakest check is %r at %d of %d." % (worst, totals[worst], n))
    print("Which failure would a customer notice first - and which would you never find out about?")
search_server.stop()
