"""
13 - Your search becomes a server.

Every tool you have written so far lives inside your agent. If the team next door wants your search,
they copy your file. Then your file changes and theirs does not.

MCP - the Model Context Protocol - is the agreement that stops that. You put the tool behind a small
server. The server DESCRIBES ITSELF: name, what each tool does, what arguments it takes. Any agent that
speaks MCP - yours, a colleague's, Claude, an IDE - can discover it and call it, knowing nothing about
your code.

The surprise in this file is how little there is to it. The schema other programs read is generated from
your function's signature and its docstring. Your type hints are the API.

Run:  python 13_mcp_server.py --check     (starts itself and prints what it tells the world)
      python 13_mcp_server.py             (runs as a server and waits - Ctrl+C to stop)
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from mcp.server.fastmcp import FastMCP
from utils.kb_search import KnowledgeBase

mcp = FastMCP("lumo-knowledge")

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))
kb = KnowledgeBase(chunks)

ORDERS = {                                               # a stand-in for the orders system
    "LM-1001": ("shipped", "arrives Tuesday, courier reference DXB-44821"),
    "LM-1002": ("packing", "leaves our Dubai warehouse tomorrow"),
    "LM-1003": ("delivered", "signed for on 12 November"),
    "LM-1004": ("held", "the address could not be verified - we have emailed the customer"),
}


# ---- TODO 1: publish the search ----------------------------------------------------------------
# The decorator is what turns a function into a tool other programs can find. Everything the outside
# world will ever know about this tool comes from three places and nowhere else:
#     the function NAME            -> the tool name
#     the TYPE HINTS               -> the argument schema (and whether an argument is required)
#     the DOCSTRING, first line    -> the description an agent reads when deciding whether to call it
#
# TODO 1 - put the decorator on, and write the docstring as if for a stranger who cannot see your code.
# HINT:  @mcp.tool()
#        and a docstring like:
#        """Search the Lumo product knowledge base. Returns the best matching passages, each tagged
#        with its [id]. Use it for questions about products, warranties, delivery and error codes."""
# (no decorator yet - add it here)
def search_knowledge(question: str, top_k: int) -> str:              # <- TODO 3 is about this line
    """TODO 1: describe this tool."""
    found = kb.search(question, k=top_k)
    if not found:
        return "NO_MATCH"
    return "\n".join("[%s] %s" % (chunk_id, text) for chunk_id, text in found)


# ---- TODO 3: your type hints ARE the API -------------------------------------------------------
# Look at the signature of search_knowledge above. `top_k: int` with no default means the schema says
# top_k is REQUIRED - so every caller in the world must now pass it, including callers who have no idea
# what a sensible k is. Give it a default and it becomes optional, and the default lives in ONE place:
# your server.
#
# TODO 3 - make top_k optional, with a sensible default.
# HINT:  def search_knowledge(question: str, top_k: int = 3) -> str:
#
# ---- TODO 2: a second tool ---------------------------------------------------------------------
# One tool is a function. Two tools is a SERVER: now an agent has to choose between them, and it chooses
# using nothing but the names, the type hints and the descriptions you write here.
#
# TODO 2 - publish check_order_status the same way: the decorator, and a docstring that makes it obvious
#          when to use this one INSTEAD of search_knowledge.
# HINT:  @mcp.tool()
#        """Look up the delivery status of one Lumo order by its order id, for example LM-1001.
#        Use this for "where is my order" questions. It cannot answer questions about products."""
# (no decorator yet - add it here)
def check_order_status(order_id: str) -> str:
    """TODO 2: describe this tool."""
    found = ORDERS.get(order_id.strip().upper())
    if not found:
        return "NO_SUCH_ORDER: there is no order %s" % order_id
    status, detail = found
    return "Order %s is %s: %s" % (order_id.strip().upper(), status, detail)


# ---- Run it ------------------------------------------------------------------------------------
if "--check" in sys.argv:
    # Start a copy of this very file as a server and ask it what it offers - exactly what any other
    # program would see. (utils/mcp_kit.py hides the asyncio; read it when you are curious.)
    from utils.mcp_kit import McpServer

    try:
        server = McpServer(os.path.abspath(__file__))
    except RuntimeError as e:
        print("The server did not start:\n   %s" % e)
        print("\nIf you have not changed anything yet, check that  pip install mcp  worked,")
        print("and that OPENAI_API_KEY is in the .env at the root of the repo (the search needs it).")
        sys.exit(0)
    print(server.describe())
    print()
    tools = {t["name"]: t for t in server.tools}
    checks = [
        ("search_knowledge is published", "search_knowledge" in tools),
        ("check_order_status is published", "check_order_status" in tools),
        ("search_knowledge has a real description",
         len(tools.get("search_knowledge", {}).get("description", "")) > 40),
        ("check_order_status has a real description",
         len(tools.get("check_order_status", {}).get("description", "")) > 40),
        ("top_k is optional, question is required",
         tools.get("search_knowledge", {}).get("schema", {}).get("required", []) == ["question"]),
    ]
    for label, ok in checks:
        print("%s  %s" % ("PASS" if ok else "FAIL", label))
    print()
    print("RESULT CHECK: %d of %d." % (sum(ok for _, ok in checks), len(checks)))
    if not tools:
        print("   TODO 1 is not done yet: the server starts, but it offers no tools at all.")
    else:
        print("Try it:", server.call("search_knowledge", question="The display says E-4210")[:120])
        print("Try it:", server.call("check_order_status", order_id="LM-1004"))
    server.stop()
    sys.exit(0)

# ---- The line that makes this a server (ready for you) -----------------------------------------
mcp.run(transport="stdio")
