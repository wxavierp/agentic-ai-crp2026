"""
BUG HUNT A - the agent keeps getting stopped for "repeating" itself.
No API key. Run:  python mechanisms/bughunt/bug_A_repeat_guard.py

RULES: first 4 minutes - NO AI. Read the SYMPTOM, then read the code, find the ONE bug.
Write in chat: (1) the line number, (2) why it causes the symptom, (3) your one-line fix.
Only then may you ask an AI - and say what it told you that you had not already found.
"""

# A scripted "model": the 5 lookups it wants to make for the goal "check stock for 5 products".
CALLS = [("check_stock", {"sku": "K10"}), ("check_stock", {"sku": "M20"}),
         ("check_stock", {"sku": "P30"}), ("check_stock", {"sku": "R40"}),
         ("check_stock", {"sku": "T50"})]


def run(calls, max_steps=8):
    seen = {}
    done = []
    for step, (name, args) in enumerate(calls, 1):
        key = name                                   # identify "the same call"
        seen[key] = seen.get(key, 0) + 1
        if seen[key] >= 3:                           # third time -> stop the agent
            return done, "repeat_guard"
        done.append(f"{name}({args['sku']})")
        if step >= max_steps:
            return done, "step_budget"
    return done, "goal_reached"


done, reason = run(CALLS)
print("calls the agent wanted to make :", len(CALLS), "(5 DIFFERENT skus - none repeated)")
print("calls actually made            :", done)
print("stop_reason                    :", reason)
print("\nSYMPTOM: stopped for repeating although no call was repeated. Expected: goal_reached with 5 calls.")
