"""
15 - Two servers, and the edge of what you can see.

Your agent now uses tools from somebody else's process. Add a second server and it uses tools from TWO
processes - and you did not write either of them, you just connected.

That is the promise of MCP. Here is the bill that comes with it: your trace stops at your own process.
LangSmith shows that your agent called a tool; it cannot see inside a program it did not run. A tool
behind a server is a black box unless you deliberately write down what crossed the boundary.

Two TODOs. One makes the agent work with two servers. One makes the boundary visible.

Run:  python 15_two_servers.py          (needs OPENAI_API_KEY and LANGSMITH_API_KEY in your .env)
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from utils.llm_client import LLMClient
from utils.mcp_kit import McpServer
from langsmith import traceable

client = LLMClient()

# Two separate processes. Neither of them is in this file.
SERVERS = [McpServer(os.path.join(HERE, "mcp_lumo_server.py")),
           McpServer(os.path.join(HERE, "mcp_tickets_server.py"))]
for s in SERVERS:
    print(s.describe())
    print()


# ---- TODO 1: which server owns which tool? -----------------------------------------------------
# With one server you could send every call to it. With two you cannot: open_ticket lives on one and
# search_knowledge on the other, and the model does not know or care which.
# So: ask each server what it offers, once, at startup, and remember who said what.
#
# TODO 1 - build a dict from tool name to the server that published it.
# HINT:  owner = {}
#        for server in SERVERS:
#            for tool in server.tools:
#                owner[tool["name"]] = server
#        return owner
def build_owners():
    owner = {}
    for server in SERVERS:
        for tool in server.tools:
            owner[tool["name"]] = server
    return owner


OWNER = build_owners()


def tool_schemas():
    """Every tool from every server, in the shape the chat API wants. (Ready-made - Lab 2's TODO 1.)"""
    return [{"type": "function",
             "function": {"name": t["name"], "description": t["description"], "parameters": t["schema"]}}
            for server in SERVERS for t in server.tools]


# ---- TODO 2: make the boundary visible ---------------------------------------------------------
# Without a decorator here, your trace says "the agent produced an answer" and the four seconds it spent
# waiting on another process are simply missing. You cannot instrument somebody else's server. You CAN
# write down, on your side, exactly what you sent and exactly what came back.
#
# TODO 2 - make this one step in the trace, and record WHICH SERVER it went to.
# HINT:  @traceable(name="mcp call", metadata={"boundary": "mcp"})
#        ...and inside, after you find the server, attach the detail:
#        from langsmith import get_current_run_tree
#        run = get_current_run_tree()
#        if run: run.metadata.update({"server": server.name, "tool": name})
@traceable(name="mcp call", metadata={"boundary": "mcp"})
def run_tool(name, arguments):
    server = OWNER.get(name)
    if server is None:
        return "NO_SUCH_TOOL: no connected server offers %r" % name
    try:
        from langsmith import get_current_run_tree
        run = get_current_run_tree()
        if run is not None:
            run.metadata.update({"server": server.name, "tool": name})
    except Exception:
        pass
    return server.call(name, **arguments)


RULES = """You are the Lumo support desk.
Use search_knowledge for questions about products, warranties, delivery times and error codes.
Use check_order_status when the customer asks where a specific order is and gives an order id.
Use list_tickets before opening a new one, and open_ticket when the customer reports a problem that
looking something up cannot fix - damage, a complaint, or a change they want made.
Answer only from what the tools return, and put the [id] after every fact that has one.
Two sentences, friendly and plain."""

MAX_STEPS = 5


@traceable(name="lumo-desk-mcp")
def ask(question):
    messages = [{"role": "system", "content": RULES}, {"role": "user", "content": question}]
    used = []
    for _ in range(MAX_STEPS):
        result = client.chat(messages, tools=tool_schemas() or None)
        if not result.tool_calls:
            return result.text or "", used
        messages.append(result.raw_message)
        for call in result.tool_calls:
            used.append(call.name)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": run_tool(call.name, call.arguments)})
    return "I could not finish that in %d steps." % MAX_STEPS, used


# ---- Run it ------------------------------------------------------------------------------------
TESTS = [
    ("The display says E-4210. What should I do?",                      "lumo-knowledge"),
    ("Where is my order LM-1002?",                                      "lumo-knowledge"),
    ("My Orion X2 from order LM-1003 arrived with a cracked case.",     "lumo-tickets"),
    ("What has already been raised about order LM-1004?",               "lumo-tickets"),
]

tracing = os.getenv("LANGSMITH_TRACING", "").lower() == "true"
print("Tracing:", "ON" if tracing else "OFF - set LANGSMITH_TRACING=true to see the boundary in LangSmith")
print("Tools discovered: %d from %d servers" % (len(tool_schemas()), len(SERVERS)))
print()

right = 0
for question, expected_server in TESTS:
    answer, used = ask(question)
    servers_hit = {OWNER[u].name for u in used if u in OWNER}
    ok = expected_server in servers_hit
    right += ok
    print("Q:", question)
    print("   tools   :", used or "none")
    print("   servers :", sorted(servers_hit) or "none", "  expected %s  %s" % (expected_server, "OK" if ok else "WRONG"))
    print("   answer  :", (answer or "").replace("\n", " ")[:140])
    print()

print("RESULT CHECK 1: the right SERVER was used in %d of %d questions." % (right, len(TESTS)))
print("RESULT CHECK 2: %d tools from %d servers, and this file contains none of them."
      % (len(tool_schemas()), len(SERVERS)))
if not OWNER:
    print("   TODO 1 is not done yet: nothing knows which server owns which tool, so every call fails.")
print()
print("Now open LangSmith. Under each run you should see 'mcp call' steps - and their metadata should")
print("say WHICH server each one went to. That line of metadata is the only thing standing between you")
print("and a black box.")

for s in SERVERS:
    s.stop()
