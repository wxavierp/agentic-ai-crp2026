"""Day 10 demo - guards + approval + reflection + eval on the Support Desk. Needs a real LLM key.

Run:  python example_support_desk/demo_day3.py
Part 1: suggested goals, then a chat loop - reflection runs on every turn; reply to the agent's
        questions or follow up. Press Enter on its own to finish.
Part 2: (optional) the fixed 5-task golden eval - fixed on purpose, an eval must be repeatable.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from project import make_agent
from kit_agent import ask_human
from kit_reflect import reflect
from kit_eval import run_eval
from utils.cli import converse

HERE = os.path.dirname(os.path.abspath(__file__))

# A rubric must fit ANY goal the user types, so it is about grounding, not one task.
RUBRIC = [
    "Answers what the user asked, OR asks ONE clear question if required information is missing",
    "Every id, status and number in the answer appears in the EVIDENCE (tool results)",
    "Does not claim an action happened (ticket, refund) unless a tool result shows it",
]

def verifier(answer, agent):
    """CODE checks first - cheap and reliable."""
    problems = []
    used = [s["action"] for s in agent.trace if s["action"]]
    if "create_ticket" in used and "T-" not in (answer or ""):
        problems.append("a ticket was created but the answer does not give the ticket number")
    return problems

SUGGESTIONS = [
    "Open a ticket for omar@example.com: 'order B200 is delayed'. Tell me the ticket number.",
    "Find which of asha@example.com's orders is delayed, open a ticket for it, and tell me the ticket number and order id.",
]

if __name__ == "__main__":
    def run_once(text):
        agent = make_agent(approve=None)               # None = risky tools are always denied
        out = reflect(agent, text, RUBRIC, verifier=verifier, budget=2)
        print("\nFINAL:", out["answer"])
        print("STATUS:", out["status"], "| REPORT:", agent.report)
        return out["answer"]

    converse(run_once, SUGGESTIONS)

    # 2) the whole golden set, with refunds auto-denied (never approve in an eval!)
    try:
        go = input("\nRun the fixed 5-task golden eval now? [Y/n] ").strip().lower()
    except EOFError:
        go = "n"
    if go in ("", "y", "yes"):
        run_eval(lambda: make_agent(approve=None),
                 tasks_path=os.path.join(HERE, "golden_tasks.json"), label="support-desk v1",
                 out=os.path.join(HERE, "eval_report.json"))
