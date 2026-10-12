"""Prints the sample output shown on the Day 9 / Day 10 demo slides (scripted fake LLM; no keys)."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_kit import *     # FakeClient, call, say, use, P, run_plan, reflect, run_eval

print("##### DAY 9 - plan, execute, re-plan #####")
plan1 = json.dumps({"steps": [
  {"id": 1, "task": "Find the customer id for asha@example.com", "tool": "find_customer"},
  {"id": 2, "task": "List her orders and pick the delayed one", "tool": "get_orders"},
  {"id": 3, "task": "Open a ticket about the delayed order", "tool": "create_ticket"}]})
chats = [use("", call("find_customer", email="asha@example.com")), say("Customer id is C-204"),
         use("", call("get_orders", customer_id="C-204")), say("Delayed order: A101"),
         use("", call("create_ticket", customer_id="C-204", issue="Order A101 delayed")), say("Ticket T-1001 created")]
a = P.make_agent(client=FakeClient(chats, [plan1, "Order A101 is delayed. Ticket T-1001 has been opened for Asha (C-204)."]))
out = run_plan(a, "Customer asha@example.com says an order is late...")
print("FINAL:", out["answer"]); print("STATUS:", out["status"], "| re-plans:", out["replans"])

print("\n##### DAY 10 - reflection + approval + eval #####")
def verifier(ans, ag):
    used = [s["action"] for s in ag.trace if s["action"]]
    return [] if "create_ticket" not in used or "T-" in ans else ["a ticket was created but the answer does not give the ticket number"]
chats = [use("", call("find_customer", email="omar@example.com")),
         use("", call("create_ticket", customer_id="C-310", issue="order B200 delayed")),
         say("I have opened a ticket for Omar."), say("Ticket T-1001 was created for Omar (C-310).")]
a = P.make_agent(client=FakeClient(chats, [json.dumps({"verdict": "CONFIRM", "issues": []})]))
out = reflect(a, "Open a ticket for omar@example.com ...", rubric=["States the ticket id", "No unsupported claims"], verifier=verifier)
print("STATUS:", out["status"], "| rounds:", out["rounds"]); print("REPORT:", a.report)

a = P.make_agent(client=FakeClient([use("Refund requested.", call("issue_refund", order_id="A101", amount=90)),
                                    say("I could not issue the refund: it needs human approval.")]), approve=None)
a.run("Refund order A101 for 90 AED right now.")
print("\nREFUND OBSERVATION:", a.trace[0]["observation"]); print("REPORT:", a.report)
