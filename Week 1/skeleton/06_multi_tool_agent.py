"""
06 · Multi-tool agent + safe execution.  (NEW · builds on 04)

One tool is a toy. Real agents pick the RIGHT tool from several. Here the agent
has TWO tools and must choose between them to finish a task:

    price_lookup[item]   -> look a price up in a small catalogue
    calc[expression]     -> do the arithmetic  (SAFELY — no eval!)

Example goal: "What is the total price of 3 widgets and 2 gadgets?"
  -> price_lookup[widget] = 25
  -> price_lookup[gadget] = 40
  -> calc[3*25 + 2*40]    = 155

SAFETY: in Lab 3 we used eval() on model output — fine for a classroom, never
in production (a model can be tricked into running dangerous code). Here you'll
build calc() on a tiny, locked-down expression parser instead. That instinct —
never trust model output blindly — is the whole of Module 7 (guardrails).

WHERE THIS GOES: choosing between tools previews Module 2 (tool use /
function calling); locking down execution previews Module 7 (guardrails).

-------------------------------------------------------------------
YOUR TASKS
  TODO 1 · finish safe_calc(): use the AST parser (started for you) so ONLY
           +  -  *  /  ( )  and numbers are allowed — no names, no calls.
  TODO 2 · finish dispatch(): route "price_lookup" and "calc" to their functions.
  TODO 3 · in the loop, parse  tool[arg]  generically and call dispatch().
-------------------------------------------------------------------
Run it:  python skeleton/06_multi_tool_agent.py
Stuck?   trainer/06_multi_tool_agent.py has the full version.
"""

import sys, os, re, ast, operator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.llm_client import LLMClient

# --- a tiny catalogue our first tool reads from ---
CATALOGUE = {"widget": 25, "gadget": 40, "sprocket": 12, "bolt": 3}

# --- allowed math operators for the SAFE calculator ---
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.USub: operator.neg}


def price_lookup(item: str):
    """Tool 1: return the catalogue price, or an error string."""
    item = item.strip().lower()
    return CATALOGUE.get(item, f"error: no price for '{item}'")


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("unsupported or unsafe expression")


def safe_calc(expression: str):
    """
    Tool 2: evaluate arithmetic WITHOUT eval().
    TODO 1: parse `expression` to an AST and walk it with _eval_node().
            Hint: tree = ast.parse(expression, mode="eval"); then _eval_node(tree.body)
            Wrap it so a bad expression returns "error: ..." instead of crashing.
    """
    # TODO 1: replace the stub below
    return "error: safe_calc not implemented yet"


def dispatch(tool: str, arg: str):
    """
    TODO 2: return the result of the right tool for `tool`:
        "price_lookup" -> price_lookup(arg)
        "calc"         -> safe_calc(arg)
        anything else  -> "error: unknown tool"
    """
    # TODO 2
    return "error: dispatch not implemented yet"


SYSTEM = """You are a reasoning agent with TWO tools:
  price_lookup[item]   -> the price of one item from the catalogue
  calc[expression]     -> evaluate a math expression (numbers and + - * / only)

At EACH step reply with EXACTLY ONE line:
  ACTION: <tool>[<argument>]
  FINAL: <the final answer>
Take ONE action at a time and use the observations you are given.
"""

MAX_STEPS = 8


def run_agent(goal: str):
    print(f"\nGOAL: {goal}\n" + "-" * 60)
    client = LLMClient()
    history = ""
    for step in range(1, MAX_STEPS + 1):
        prompt = f"Task: {goal}\n{history}\nWhat is your next step?"
        response = client.get_completion(prompt, system_message=SYSTEM,
                                         temperature=0.0, max_tokens=200)
        line = (response or "").strip().splitlines()[0].strip() if response else ""
        print(f"[step {step}] {line}")

        if line.upper().startswith("FINAL:"):
            return line.split(":", 1)[1].strip()

        # TODO 3: match a generic  tool[arg]  (e.g. price_lookup[widget] or calc[3*25]),
        #         call dispatch(tool, arg), print the observation and append it to history.
        #         If no valid action is found, nudge the model to use ACTION:/FINAL:.
        pass  # TODO 3

    return "Stopped: reached the step limit."


if __name__ == "__main__":
    goal = "What is the total price of 3 widgets and 2 gadgets?"
    print("FINAL:", run_agent(goal))
