"""Day 9 demo - plan-then-execute on the Support Desk project. Needs a real LLM key (Groq free).

Run:  python example_support_desk/demo_day2.py
It shows suggested goals and waits. After each answer you can REPLY - answer the agent's
question, ask a follow-up, or give a new goal. Press Enter on its own to finish.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from project import make_agent
from kit_planner import run_plan, ask_plan_ok
from utils.cli import converse

SUGGESTIONS = [
    "Customer asha@example.com says an order is late. Find the delayed order, open a ticket "
    "for her about it, and tell me the ticket number and order id.",
    "Customer omar@example.com asks whether his order B200 can ship. Check the item's stock and, "
    "if it is out of stock, open a backorder ticket and tell me the ticket number.",
]

if __name__ == "__main__":
    def run_once(text):
        agent = make_agent()                           # fresh agent each turn (history is in the text)
        out = run_plan(agent, text, approve_plan=None)   # try approve_plan=ask_plan_ok for a human gate
        print("\nFINAL:", out["answer"])
        print("STATUS:", out["status"], "| re-plans:", out["replans"])
        return out["answer"]

    converse(run_once, SUGGESTIONS)
