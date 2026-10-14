"""
BUG HUNT B - the reflection loop approved a WRONG answer.
No API key. Run:  python mechanisms/bughunt/bug_B_verifier.py

RULES: first 4 minutes - NO AI. Find the ONE bug (line + why + one-line fix) before asking anything.
"""
import re

# What the tools really returned (the trace)
TRACE = [
    {"action": "find_customer",  "args": {"email": "asha@example.com"}, "observation": "C-7 Asha"},
    {"action": "get_orders",     "args": {"customer_id": "C-7"},        "observation": "O-55 delayed"},
    {"action": "create_ticket",  "args": {"order_id": "O-55"},          "observation": "created ticket T-1002"},
]
# What the agent SAID (a typical hallucination: wrong ticket number)
ANSWER = "I opened ticket T-1001 for order O-55."


def verifier(answer, trace):
    """Code check: every ticket id in the answer must appear in a create_ticket observation."""
    claimed = re.findall(r"T-\d", answer)
    real = [step["observation"] for step in trace if step["action"] == "create_ticket"]
    problems = []
    for t in claimed:
        if not any(t in obs for obs in real):
            problems.append(f"{t} was never returned by create_ticket")
    return problems


problems = verifier(ANSWER, TRACE)
print("answer  :", ANSWER)
print("reality :", TRACE[-1]["observation"])
print("verifier problems:", problems or "none -> status CONFIRMED")
print("\nSYMPTOM: the answer is wrong (T-1001 vs T-1002) yet the verifier says everything is fine.")
