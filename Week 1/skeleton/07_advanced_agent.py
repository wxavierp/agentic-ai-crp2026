"""
07 · ADVANCED TRACK — native function calling.  (optional · for fast finishers)

In Labs 3–6 the agent chose tools by writing text like  ACTION: calc[...]  and
we parsed it with a regex. That works, but every serious provider now offers
NATIVE FUNCTION / TOOL CALLING: you describe your tools as JSON schemas, and the
model returns a structured, validated tool call — no fragile string parsing.
This is exactly what Module 2 (Tool Use & Function Calling) is about; you're
getting a head start.

    You  ->  give the model a `tools` schema
    Model ->  returns tool_calls (name + JSON arguments)
    You  ->  run the tool, hand back the result, loop until it stops

This file targets the OpenAI / Groq chat-completions tools API (same shape).
Set LLM_PROVIDER=openai or groq in your .env.

-------------------------------------------------------------------
YOUR TASKS  (tiered — do as many as you can)
  TODO 1 · describe the calculator as a JSON tool schema (TOOLS).
  TODO 2 · run the loop: send messages+tools; if the model returns tool_calls,
           execute each and append a tool result message; else print the answer.

  STRETCH CHALLENGES (see CHALLENGES at the bottom) — reflection, a 2nd tool,
  AST-safe execution, malformed-argument handling, and an MCP write-up.
-------------------------------------------------------------------
Run it:  python skeleton/07_advanced_agent.py
Reference: trainer/07_advanced_agent.py
"""

import sys, os, json, ast, operator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.llm_client import LLMClient

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg}

def _ev(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)): return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in _OPS: return _OPS[type(n.op)](_ev(n.left), _ev(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS: return _OPS[type(n.op)](_ev(n.operand))
    raise ValueError("unsafe expression")

def calculator(expression: str):
    """AST-safe calculator (no eval)."""
    return _ev(ast.parse(expression, mode="eval").body)


# TODO 1: describe the calculator tool as an OpenAI/Groq tool schema.
#   It's a list of dicts: [{"type":"function","function":{"name","description","parameters"}}]
#   parameters is a JSON-schema object with one string property "expression".
TOOLS = []   # TODO 1


def run_agent(goal: str):
    client = LLMClient()
    if client.provider not in ("openai", "groq"):
        print("This advanced demo targets LLM_PROVIDER=openai or groq.")
        return
    sdk = client.client                      # the raw OpenAI/Groq SDK client
    model = client._default_model()
    messages = [{"role": "user", "content": goal}]

    for step in range(1, 9):
        # TODO 2a: call sdk.chat.completions.create(model=model, messages=messages,
        #          tools=TOOLS, temperature=0.0) and read msg = resp.choices[0].message
        msg = None   # TODO 2a
        if msg is None:
            print("Complete TODO 2 to run the loop."); return

        if not getattr(msg, "tool_calls", None):
            print("FINAL:", msg.content)
            return msg.content

        messages.append(msg)   # record the assistant's tool request
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            print(f"[step {step}] {tc.function.name}({args})")
            # TODO 2b: run calculator(args["expression"]), then append a tool result:
            #   messages.append({"role":"tool","tool_call_id":tc.id,"content":str(result)})
            pass  # TODO 2b

    print("Stopped: step limit.")


if __name__ == "__main__":
    run_agent("What is (23 * 7) + 19? Use the calculator tool, then give the final number.")


# ============================ CHALLENGES ============================
# Level 1  · Add a second tool (e.g. price_lookup) with its own schema and let
#            the model choose. (previews Module 2)
# Level 2  · Add a REFLECT step: after the model's final answer, ask it to CONFIRM
#            or REVISE, and loop on REVISE. (previews Modules 3–4 & 7)
# Level 3  · Harden it: validate tool arguments, catch bad JSON, and keep the
#            AST-safe calculator — never eval() model output. (previews Module 7)
# Level 4  · Write 8–10 lines on how MCP (Model Context Protocol) would replace
#            these hand-written schemas with a shared tool server your agent
#            connects to. (previews Module 6: Multi-Agent + MCP)
# ===================================================================
