"""
Mechanism 2 - budgets and the repeat guard: which one stops the agent, and when?
No API key. Run:  python mechanisms/m2_guards_naked.py

PREDICT FIRST: for each configuration below, at which STEP does the run stop, and which
guard fires?  (A confused model keeps asking the same questions forever.)
"""
import itertools

SAME   = itertools.cycle([("check_stock", {"sku": "K10"})])                         # K10, K10, K10, ...
ALTERN = itertools.cycle([("check_stock", {"sku": "K10"}), ("check_stock", {"sku": "M20"})])   # K10, M20, K10, M20, ...


def run(calls, max_steps=8, repeat_guard=False, max_tool_calls=99):
    seen, tool_calls = {}, 0
    for step in range(1, max_steps + 1):
        name, args = next(calls)
        key = (name, tuple(sorted(args.items())))
        seen[key] = seen.get(key, 0) + 1
        if repeat_guard and seen[key] >= 3:                 # 1st check: repeats
            return step, "repeat_guard"
        if tool_calls >= max_tool_calls:                    # 2nd check: cost
            return step, "tool_budget"
        tool_calls += 1                                     # ... the tool runs here ...
    return max_steps, "step_budget"


CONFIGS = [
    ("A  same call forever, only max_steps=8",          lambda: run(SAME)),
    ("B  same call forever, repeat guard on",           lambda: run(SAME, repeat_guard=True)),
    ("C  same call forever, max_tool_calls=2",          lambda: run(SAME, max_tool_calls=2)),
    ("D  K10/M20 alternating, repeat guard on",         lambda: run(ALTERN, repeat_guard=True)),
    ("E  K10/M20 alternating, guard on + max_tool_calls=4", lambda: run(ALTERN, repeat_guard=True, max_tool_calls=4)),
]
for label, fn in CONFIGS:
    step, reason = fn()
    print(f"{label:55s} -> stops at step {step}  ({reason})")

print("\nQUESTIONS: (1) why does D stop at step 5, not 3?   (2) in E two guards trip on the same step - "
      "which wins, and what decides that?")
