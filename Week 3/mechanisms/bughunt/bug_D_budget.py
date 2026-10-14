"""
BUG HUNT D - "max_tool_calls = 3" but the agent made 4 calls.
No API key. Run:  python mechanisms/bughunt/bug_D_budget.py

RULES: first 4 minutes - NO AI. Find the ONE bug (line + why + one-line fix) before asking anything.
"""
import itertools

CALLS = itertools.cycle([("check_stock", {"sku": "K10"}), ("check_stock", {"sku": "M20"}),
                         ("get_orders", {"customer_id": "C-7"}), ("find_customer", {"email": "a@x.com"}),
                         ("check_stock", {"sku": "P30"})])


def run(max_steps=10, max_tool_calls=3):
    tool_calls, ran = 0, []
    for step in range(1, max_steps + 1):
        name, args = next(CALLS)
        if tool_calls > max_tool_calls:          # COST GUARD
            return ran, "tool_budget"
        ran.append(name)                         # ... the tool runs ...
        tool_calls += 1
    return ran, "step_budget"


ran, reason = run()
print("budget max_tool_calls :", 3)
print("tools that actually ran:", len(ran), ran)
print("stop_reason           :", reason)
print("\nSYMPTOM: the budget is 3 but 4 tools ran. Expected: exactly 3 tools run, then tool_budget.")
