"""
01 · Assistant vs Agent  —  the core difference, in code.  (TRAINER / full solution)

An ASSISTANT answers with words. It might guess, and it can be wrong.
An AGENT uses a TOOL to actually DO the work — so its answer is exact.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.llm_client import LLMClient


def calculator(expression: str):
    """A real tool: evaluates a math expression and returns the exact number."""
    # Locked-down eval: no builtins, no variables — just arithmetic.
    return eval(expression, {"__builtins__": {}}, {})


def main():
    client = LLMClient()

    task = "What is 18.5% of 2480, plus 365? Give only the final number."

    print("=" * 60)
    print(" (A) ASSISTANT — answers in words (may be wrong)")
    print("=" * 60)
    assistant_answer = client.get_completion(task, temperature=0.0)
    print(assistant_answer, "\n")

    print("=" * 60)
    print(" (B) AGENT — uses the calculator tool (exact)")
    print("=" * 60)
    expression = "0.185 * 2480 + 365"
    tool_result = calculator(expression)
    print(f"calculator({expression!r}) = {tool_result}\n")

    print("-" * 60)
    print("ANALYSIS: The assistant produced text; the agent RAN CODE.")
    print("Only the agent's answer is guaranteed correct — that's why agents use tools.")
    print(f"(Exact answer: {tool_result})")


if __name__ == "__main__":
    main()
