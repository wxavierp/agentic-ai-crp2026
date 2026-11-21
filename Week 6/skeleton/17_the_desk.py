"""
17 - The whole desk.

Everything from this week, in one file:
    a supervisor that routes                      (Session 17)
    specialists with their own rules              (Session 17, 18)
    search that lives in another process          (Session 19, over MCP)
    an escalation that leaves Python entirely     (Session 20, over n8n)
    all of it traced                              (Session 17, LangSmith)

That is the shape of a production desk. Nothing here is new except the assembling - which is the part
nobody teaches, and the part that is actually hard.

Run:  python 17_the_desk.py          (needs OPENAI_API_KEY, LANGSMITH_API_KEY; N8N_WEBHOOK_URL optional)
"""
import os, sys, json, time
from typing import TypedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from utils.llm_client import LLMClient
from utils.graph_kit import StateGraph, END, USING
from utils.mcp_kit import McpServer
from utils.n8n_kit import post_to_n8n, USING as N8N_USING
from langsmith import traceable

client = LLMClient()
search_server = McpServer(os.path.join(HERE, "mcp_lumo_server.py"))
DESTINATIONS = ["warranty", "technical", "escalate"]


@traceable(name="ask_model")
def ask_model(rules, message):
    return client.get_completion(message, system_message=rules, temperature=0)


@traceable(name="mcp search")
def search(question):
    return search_server.call("search_knowledge", question=question)


SUPERVISOR_RULES = """You are the supervisor of the Lumo support desk. You never answer the customer.
Read the question and name the ONE destination that should handle it.

warranty   - warranty cover, guarantees, returns, refunds
technical  - error codes, charging, how a device is used
escalate   - the customer reports damage, a complaint, something lost or late, or anything a human must
             act on. Also use this when they give an order id and are unhappy.

Answer with exactly one word: warranty, technical or escalate. No punctuation, no explanation."""

ANSWER_RULES = """You are a specialist on the Lumo support desk.
Answer ONLY from the search results you are given, and put the [id] after every fact.
If the results do not answer it, reply exactly: I don't know.
Two sentences, friendly and plain."""


# ---- TODO 1: the route map ---------------------------------------------------------------------
# Session 17 again, with a third destination. Remember the safe default: anything the supervisor says
# that is not one of the three is a surprise, and a surprise must not crash a customer's question.
#
# TODO 1 - complete the map, and make route() fall back to "escalate" for anything unexpected.
#          (Why escalate and not warranty? Because when you do not know what this is, a human should see it.)
# HINT:  ROUTES = {"warranty": "warranty", "technical": "technical", "escalate": "escalate"}
#        and in route():  return state["destination"] if state["destination"] in DESTINATIONS else "escalate"
ROUTES = {"warranty": "warranty", "technical": "warranty", "escalate": "warranty"}   # <- replace this line


def route(state):
    return "warranty"                                   # <- replace this line


# ---- TODO 2: the escalation node ---------------------------------------------------------------
# The other two nodes answer. This one does something OUTSIDE Python and then tells the customer the
# truth about whether it worked - which is the rule you wrote in 16.
#
# TODO 2 - send it to n8n and build the reply from what came back.
# HINT:  answer = post_to_n8n({"order_id": state.get("order_id") or "unknown",
#                              "reason": "the desk could not answer this",
#                              "question": state["question"]})
#        if answer.get("ok"):
#            reply = "I have passed this to a colleague (%s). %s" % (answer.get("ticket"), answer.get("message", ""))
#        else:
#            reply = "I could not reach our support system just now, so nothing has been logged yet. Please quote %s when you contact us." % (state.get("order_id") or "your order number")
#        return {"reply": reply, "escalated": bool(answer.get("ok")), "path": state["path"] + ["escalate"]}
def escalate_node(state):
    return {"reply": "TODO 2 is not done yet.", "escalated": False,
            "path": state["path"] + ["escalate"]}       # <- replace these lines


# ---- The rest of the graph (ready for you) -----------------------------------------------------
class State(TypedDict, total=False):
    question: str
    order_id: str
    destination: str
    reply: str
    escalated: bool
    path: list


def supervise_node(state):
    said = ask_model(SUPERVISOR_RULES, state["question"]).strip().lower()
    return {"destination": said, "path": state["path"] + ["supervise"]}


def answer_node(name):
    def node(state):
        results = search(state["question"])
        reply = ask_model(ANSWER_RULES, "Customer question: %s\n\nSearch results:\n%s"
                          % (state["question"], results))
        return {"reply": reply, "escalated": False, "path": state["path"] + [name]}
    return node


graph = StateGraph(State)
graph.add_node("supervise", supervise_node)
graph.add_node("warranty", answer_node("warranty"))
graph.add_node("technical", answer_node("technical"))
graph.add_node("escalate", escalate_node)
graph.set_entry_point("supervise")
graph.add_conditional_edges("supervise", route, ROUTES)
for name in DESTINATIONS:
    graph.add_edge(name, END)
workflow = graph.compile()


@traceable(name="lumo-desk")
def ask(question, order_id=None):
    return workflow.invoke({"question": question, "order_id": order_id, "path": []},
                           config={"run_name": "lumo-desk", "tags": ["session-20"],
                                   "metadata": {"order_id": order_id}})


# ---- Run it ------------------------------------------------------------------------------------
TESTS = [
    ("How long is the warranty on the Falcon S2 Pro?",              None,      "warranty"),
    ("The display says E-4210. What should I do?",                  None,      "technical"),
    ("My Orion X2 from order LM-1003 arrived with a cracked case.", "LM-1003", "escalate"),
]

print("Graph engine :", USING)
print("Escalation   :", N8N_USING)
print("Search       : %s (a separate process)" % search_server.name)
print()

right = 0
started = time.time()
for question, order_id, expected in TESTS:
    final = ask(question, order_id)
    went = final["path"][-1]
    ok = went == expected
    right += ok
    print("Q:", question)
    print("   path     :", " -> ".join(final["path"]))
    print("   expected :", expected, "  %s" % ("OK" if ok else "WRONG"))
    print("   reply    :", (final.get("reply") or "").replace("\n", " ")[:150])
    print()

print("RESULT CHECK 1: %d of %d questions reached the right destination." % (right, len(TESTS)))
print("RESULT CHECK 2: the desk used %d destinations - a 1 here means TODO 1 is not done."
      % len(set(ROUTES.values())))
print("RESULT CHECK 3: all three took %.1f seconds in total." % (time.time() - started))
search_server.stop()
