"""Predict-then-run on the Support Desk. Needs a real LLM key.   python example_support_desk/demo_predict.py

You write a prediction (steps / tools / stop reason) BEFORE the agent runs; it is saved with a
timestamp; then the agent runs and you get a scorecard. Keep going: each turn is a new prediction.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from project import make_agent
from kit_predict import predict_then_run
from utils.cli import converse

SUGGESTIONS = [
    "What is the status of order A100?",
    "Find which of asha@example.com's orders is delayed, open a ticket for it, and tell me the ticket number.",
]

if __name__ == "__main__":
    def run_once(text):
        agent = make_agent(approve=None)
        # the prediction is about the FIRST message of this turn, so show it to the student
        out = predict_then_run(agent, text)
        print("\nANSWER:", out["answer"])
        return out["answer"]
    converse(run_once, SUGGESTIONS)
