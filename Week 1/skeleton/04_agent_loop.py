"""
04 · Build the agent loop  —  observe -> reason -> act -> evaluate.

   >>> THE ONE REAL CODING EXERCISE OF WEEK 1. <<<

You'll complete a minimal but REAL agent. Given a goal, it loops:
    OBSERVE   assemble the prompt from the goal + what has happened so far
    REASON    the LLM decides the next step (an ACTION, or a FINAL answer)
    ACT       run the chosen tool (a calculator) and get a result
    EVALUATE  if the LLM said FINAL, stop; otherwise record the result and loop

The tool, the system prompt and the parsing are given to you.
You implement the FOUR steps of the loop.

-------------------------------------------------------------------
YOUR TASKS  (inside run_agent)
  TODO 1 · OBSERVE   build `prompt` from the goal + history
  TODO 2 · REASON    call the LLM to get the next step
  TODO 3 · ACT       run calculator() on the parsed expression
  TODO 4 · EVALUATE  stop on FINAL, else append the result and loop
-------------------------------------------------------------------
Run it:  python skeleton/04_agent_loop.py
Goal to solve:  "What is (23 * 7) + 19?"   (expected: 180)
Stuck? The full version is in trainer/04_agent_loop.py — try first!
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.llm_client import LLMClient


def calculator(expression: str):
    """Evaluate a math expression exactly."""
    return eval(expression, {"__builtins__": {}}, {})


SYSTEM = """You are a reasoning agent that solves a task step by step.
You have ONE tool:
  calculator[expression]  -> evaluates a math expression (e.g. calculator[23*7]).

At EACH step reply with EXACTLY ONE line, in one of these two forms:
  ACTION: calculator[<expression>]
  FINAL: <the final answer>

Take only ONE action at a time. Use the observations you are given.
"""

MAX_STEPS = 6


def run_agent(goal: str):
    print(f"\nGOAL: {goal}\n" + "-" * 60)
    client = LLMClient()
    history = ""   # the agent's MEMORY of the run

    for step in range(1, MAX_STEPS + 1):

        # 1) OBSERVE
        # TODO 1: build `prompt` from the goal + history (ask for the next step)
        prompt = ""  # TODO 1

        # 2) REASON
        # TODO 2: call client.get_completion(prompt, system_message=SYSTEM,
        #         temperature=0.0, max_tokens=200) and keep the FIRST line in `line`
        line = ""  # TODO 2
        print(f"[step {step}] {line}")

        # 4) EVALUATE (part 1): stop if the agent gave a FINAL answer
        if line.upper().startswith("FINAL:"):
            return line.split(":", 1)[1].strip()

        # 3) ACT: run the tool the agent chose
        match = re.search(r"calculator\[(.+?)\]", line)
        if match:
            expr = match.group(1)
            # TODO 3: call calculator(expr) safely; put the result (or an error
            #         string) into `result`
            result = None  # TODO 3
            print(f"        observation: calculator[{expr}] = {result}")

            # 4) EVALUATE (part 2): record the observation so the next loop sees it
            # TODO 4: append the result to `history` so the agent remembers it
            pass  # TODO 4
        else:
            history += "\n(No valid action found; reply with ACTION: or FINAL:.)"

    return "Stopped: reached the step limit without a FINAL answer."


if __name__ == "__main__":
    goal = "What is (23 * 7) + 19?"
    final = run_agent(goal)
    print("-" * 60)
    print(f"AGENT'S FINAL ANSWER: {final}")
    # Stretch: add a second tool and let the agent choose between tools.
