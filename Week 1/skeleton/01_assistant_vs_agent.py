"""
01 · Assistant vs Agent  —  the core difference, in code.

An ASSISTANT answers with words. It might guess, and it can be wrong.
An AGENT uses a TOOL to actually DO the work — so its answer is exact.

You'll ask an LLM to do a calculation two ways:
  (A) as an assistant  -> it replies in words (and may get it wrong)
  (B) as an agent      -> it calls a real calculator tool (always exact)

-------------------------------------------------------------------
YOUR TASKS
  TODO 1: Write the `task` question (a multi-step arithmetic problem).
  TODO 2: Implement the `calculator` tool so the agent can compute exactly.
Then run it and compare the two answers.
-------------------------------------------------------------------
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.llm_client import LLMClient


def calculator(expression: str):
    """
    A real tool: evaluates a math expression and returns the exact number.

    TODO 2: Implement this. Evaluate `expression` (e.g. "0.185*2480 + 365")
            and return the numeric result.
            Hint: eval(expression, {"__builtins__": {}}, {}) keeps it simple & safe-ish.
    """
    # TODO 2: replace the line below with a real evaluation
    return None


def main():
    client = LLMClient()

    # TODO 1: Write a multi-step arithmetic task, e.g. an 18.5% share plus a fixed amount.
    task = ""  # TODO 1: e.g. "What is 18.5% of 2480, plus 365? Give only the number."

    if not task:
        print("Please complete TODO 1 (write the `task`).")
        return

    print("=" * 60)
    print(" (A) ASSISTANT — answers in words (may be wrong)")
    print("=" * 60)
    assistant_answer = client.get_completion(task, temperature=0.0)
    print(assistant_answer, "\n")

    print("=" * 60)
    print(" (B) AGENT — uses the calculator tool (exact)")
    print("=" * 60)
    # The 'agent' decides to use the calculator and passes it the expression.
    expression = "0.185 * 2480 + 365"   # (matches the task above; change if your task differs)
    tool_result = calculator(expression)
    print(f"calculator({expression!r}) = {tool_result}\n")

    print("-" * 60)
    print("ANALYSIS: The assistant produced text; the agent RAN CODE.")
    print("Only the agent's answer is guaranteed correct — that's why agents use tools.")


if __name__ == "__main__":
    main()
