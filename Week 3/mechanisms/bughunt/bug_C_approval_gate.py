"""
BUG HUNT C - a refund ran although nobody approved it.
No API key. Run:  python mechanisms/bughunt/bug_C_approval_gate.py

RULES: first 4 minutes - NO AI. Find the ONE bug (line + why + one-line fix) before asking anything.
"""

RISKY = {"refund", "send_email"}                 # tools that need a human "yes"
LOG = []


def issue_refund(order_id, amount):
    LOG.append(f"REFUNDED {amount} on {order_id}")
    return f"refund of {amount} issued for {order_id}"


FUNCTIONS = {"issue_refund": issue_refund}


def run_tool(name, args, approve):
    if name in RISKY:                            # approval gate
        if not approve(name, args):
            return "error: a human did not approve this action."
    return FUNCTIONS[name](**args)


def nobody_approves(name, args):                 # the human says NO to everything
    return False


print(run_tool("issue_refund", {"order_id": "O-55", "amount": 40}, nobody_approves))
print("side effects:", LOG or "none")
print("\nSYMPTOM: the human said NO to everything, yet the money moved. Expected: blocked, side effects none.")
