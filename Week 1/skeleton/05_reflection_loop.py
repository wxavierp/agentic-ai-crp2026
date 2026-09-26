"""
05 · Reflection — make the agent check its own work.  (NEW · builds on 04)

In Lab 3 you built the loop: observe -> reason -> act -> evaluate.
Real agents add one more move: REFLECT — before trusting a final answer, the
agent critiques it and, if it isn't confident, tries again with that feedback.
This is the "Reflection" / Reflexion pattern, and it's one of the most common
reliability tricks in production agents in 2026.

    observe -> reason -> act -> evaluate -> REFLECT -> (loop again if needed)

WHERE THIS GOES: self-critique + feedback-in-memory is the seed of
Module 3 (agent architectures) and Module 4 (memory); "is the answer good
enough?" is the heart of Module 7 (evaluation & guardrails).

-------------------------------------------------------------------
YOUR TASKS  (the base loop is given — you add the reflection)
  TODO 1 · write reflect(): ask the LLM to judge the final answer and reply
           CONFIRM  or  REVISE: <what's wrong>
  TODO 2 · in run_agent(), when the agent says FINAL, call reflect().
           If it CONFIRMs, return. If it REVISEs, push the feedback into
           history and let the loop run again instead of returning.
-------------------------------------------------------------------
Run it:  python skeleton/05_reflection_loop.py     (goal solves to 180)
Stuck?   trainer/05_reflection_loop.py has the full version.
"""

import sys, os, re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.llm_client import LLMClient


def calculator(expression: str):
    return eval(expression, {"__builtins__": {}}, {})


SYSTEM = """You are a reasoning agent that solves a task step by step.
You have ONE tool:
  calculator[expression]  -> evaluates a math expression (e.g. calculator[23*7]).
At EACH step reply with EXACTLY ONE line, in one of these two forms:
  ACTION: calculator[<expression>]
  FINAL: <the final answer>
Take only ONE action at a time. Use the observations you are given.
"""

MAX_STEPS = 8


def reflect(client, goal, answer):
    """
    TODO 1: Ask the LLM to check `answer` against `goal`.
    Return the model's reply. Prompt it to respond with EXACTLY one line:
        CONFIRM
      or
        REVISE: <one sentence on what is wrong>
    Keep temperature=0.0.
    """
    # TODO 1: build a critique prompt and return client.get_completion(...)
    return "CONFIRM"   # <- replace this stub


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
            answer = line.split(":", 1)[1].strip()
            # TODO 2: reflect before you trust it.
            #   verdict = reflect(client, goal, answer)
            #   if it starts with CONFIRM -> return answer
            #   else -> add the critique to history and CONTINUE the loop
            return answer   # <- replace: only return after a CONFIRM

        match = re.search(r"calculator\[(.+?)\]", line)
        if match:
            expr = match.group(1)
            try:
                result = calculator(expr)
            except Exception as e:
                result = f"error: {e}"
            print(f"        observation: calculator[{expr}] = {result}")
            history += f"\nYou ran calculator[{expr}] and got {result}."
        else:
            history += "\n(No valid action found; reply with ACTION: or FINAL:.)"

    return "Stopped: reached the step limit without a confirmed answer."


if __name__ == "__main__":
    goal = "What is (23 * 7) + 19?"
    print("FINAL:", run_agent(goal))
