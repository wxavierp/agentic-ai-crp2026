"""
14 - The agent that did not know what it could do.

In Week 2 you wrote tool schemas by hand: name, description, a JSON block describing each argument.
They lived in your agent file. If the tool changed, you changed them, and if you forgot, the agent
started lying to the model about what the tool took.

This agent has no tool schemas. It starts an MCP server, ASKS what it offers, and builds its schemas
from the answer. Change the server - add a tool, rename an argument - and the agent picks it up with
no edit at all.

You write the three pieces that make that possible: the translation from MCP's description to the
chat API's schema, the dispatch back to the server, and the rules that keep the answers honest.

Run:  python 14_mcp_agent.py          (needs OPENAI_API_KEY in your .env · pip install mcp)
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from utils.llm_client import LLMClient
from utils.mcp_kit import McpServer

client = LLMClient()

# The server is a SEPARATE PROCESS. We did not import it; we started it and spoke to it over a protocol.
server = McpServer(os.path.join(HERE, "mcp_lumo_server.py"))
print(server.describe())
print()


# ---- TODO 1: from "what the server says" to "what the model understands" -----------------------
# server.tools is a list of dicts the SERVER gave us:
#     {"name": "search_knowledge", "description": "Search the Lumo ...", "schema": {...JSON schema...}}
# The chat API wants the same three facts in its own shape. This function is the whole bridge between
# a protocol built for tools and an API built for models - and it is six lines.
#
# TODO 1 - build one chat-API tool schema per MCP tool.
# HINT:  return [{"type": "function",
#                 "function": {"name": t["name"],
#                              "description": t["description"],
#                              "parameters": t["schema"]}}
#                for t in server.tools]
def tool_schemas():
    return []                                           # <- replace this line


# ---- TODO 2: dispatch ---------------------------------------------------------------------------
# The model does not call anything. It ASKS: "run search_knowledge with these arguments". You run it.
# In Week 2 that meant looking the name up in a dictionary of your own functions. Now it means sending
# the request to the server - and you do not need a dictionary at all, because the server has one.
#
# TODO 2 - send the call to the server and return its text.
# HINT:  return server.call(name, **arguments)
def run_tool(name, arguments):
    return "TODO 2 is not done yet: nothing was called."     # <- replace this line


# ---- TODO 3: the rules ---------------------------------------------------------------------------
# Two tools means the agent has to CHOOSE, and the only things it chooses from are the descriptions on
# the server plus these rules. Make the two cases unambiguous, and say what to do when neither fits.
#
# TODO 3 - write the rules.
# HINT:  RULES = """You are the Lumo support desk.
#        Use search_knowledge for questions about products, warranties, delivery times and error codes.
#        Use check_order_status when the customer asks where a specific order is and gives an order id.
#        Answer only from what the tools return, and put the [id] after every fact that has one.
#        If the tools return NO_MATCH or NO_SUCH_ORDER, say so plainly and do not guess.
#        Do not call a tool for a greeting. Two sentences, friendly and plain."""
RULES = """You are the Lumo support desk. Answer the customer."""      # <- replace this line


# ---- The agent loop (ready for you: this is the Week 2 loop, unchanged) -------------------------
MAX_STEPS = 4


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
    ("The display says E-4210. What should I do?",              "search_knowledge"),
    ("Where is my order LM-1004?",                              "check_order_status"),
    ("How long is the warranty on the Falcon S2 Pro?",          "search_knowledge"),
    ("Hello!",                                                  None),
]

right = 0
for question, expected in TESTS:
    answer, used = ask(question)
    chosen = used[0] if used else None
    ok = chosen == expected
    right += ok
    print("Q:", question)
    print("   tools used :", used or "none")
    print("   expected   :", expected or "none", "  %s" % ("OK" if ok else "WRONG"))
    print("   answer     :", (answer or "").replace("\n", " ")[:150])
    print()

print("RESULT CHECK 1: the agent chose the right tool in %d of %d questions." % (right, len(TESTS)))
print("RESULT CHECK 2: the agent was given %d tool(s) it discovered at run time, not ones you typed."
      % len(tool_schemas()))
if not tool_schemas():
    print("   TODO 1 is not done yet: the model was offered no tools, so it had to make everything up.")


# ---- The app (ready for you: nothing to fill in here) ------------------------------------------
import gradio as gr


def run_desk(question):
    if not question.strip():
        return "", ""
    answer, used = ask(question)
    return ", ".join(used) or "none", answer


with gr.Blocks(title="MCP desk") as app:
    gr.Markdown("## The desk, over MCP\nThe tools are not in this file. They are in another process that "
                "described itself when the agent started.")
    gr.Markdown("```\n%s\n```" % server.describe())
    box = gr.Textbox(label="Customer question", placeholder="for example: Where is my order LM-1002?")
    used_box = gr.Textbox(label="Tools the agent called")
    answer_box = gr.Textbox(label="Answer", lines=3)
    box.submit(run_desk, box, [used_box, answer_box])
    gr.Button("Ask", variant="primary").click(run_desk, box, [used_box, answer_box])
    gr.Examples([q for q, _ in TESTS], inputs=box)

app.launch(inbrowser=True)
server.stop()
