"""
16 - The agent gets a hand into the rest of the business.

Everything your desk can do so far happens inside Python. It can look things up and write a reply.
It cannot open a ticket in a real system, email a human, add a row to a sheet, or post to a channel -
and a support desk that cannot escalate is a demo.

n8n is where that work goes. You draw a workflow once - webhook in, do things, respond - and your agent
calls it like any other tool. The agent does not need credentials for the ticket system, the sheet or
the mailbox: n8n holds those, and your agent holds a URL.

BEFORE THIS LAB, build the workflow (five minutes, the README has pictures):
    Webhook (POST, path: escalate, Respond: "Using Respond to Webhook Node")
      -> Set node: ok=true, ticket={{ "N8N-" + $now.toMillis() }}, queue="human-support",
                   message="A human has been notified and will reply by email."
      -> Respond to Webhook
    Publish it, open the webhook node, copy the PRODUCTION url (/webhook/, not /webhook-test/),
    and put it in your .env as  N8N_WEBHOOK_URL=...

Run:  python 16_n8n_tool.py
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
from utils.n8n_kit import post_to_n8n, N8N_URL, USING


# ---- TODO 1: what you send ---------------------------------------------------------------------
# A webhook payload is a contract. Everything downstream in the workflow reads these field names, so
# they are an API: once a colleague's workflow depends on "order_id", renaming it breaks their work.
#
# TODO 1 - build the payload. Send the order id, why we are escalating, and what the customer asked.
# HINT:  return {"order_id": order_id, "reason": reason, "question": question}
def escalation_payload(order_id, reason, question):
    return {}                                           # <- replace this line


# ---- TODO 2: the tool the agent will call ------------------------------------------------------
# TODO 2 - send the payload and turn the answer into ONE sentence the agent can put in a reply.
#          post_to_n8n never raises: it always returns a dict, and ok tells you which way it went.
# HINT:  answer = post_to_n8n(escalation_payload(order_id, reason, question))
#        if answer.get("ok"):
#            return "Escalated as %s to %s. %s" % (answer.get("ticket"), answer.get("queue"), answer.get("message", ""))
#        return "ESCALATION FAILED: %s" % answer.get("error", "unknown")
def escalate(order_id, reason, question):
    """Hand this case to a human through the n8n workflow. Returns one sentence."""
    return "TODO 2 is not done yet: nothing was sent."  # <- replace this line


# ---- TODO 3: what the agent is told when it fails ----------------------------------------------
# An escalation that silently fails is worse than no escalation: the customer is told a human will call,
# and nobody was told anything. The agent has to be able to tell the difference, in words.
#
# TODO 3 - write the sentence the AGENT reads when escalation failed, so it says something true to the
#          customer instead of promising a call-back that will not happen.
# HINT:  FAILURE_RULE = ("If the escalation tool returns a sentence starting with ESCALATION FAILED, "
#                        "do NOT tell the customer a human has been notified. Say that you could not "
#                        "reach the support system, and give them the order id to quote.")
FAILURE_RULE = ""                                       # <- replace this line


# ---- Run it ------------------------------------------------------------------------------------
print("Sending to:", USING)
print()

CASES = [
    ("LM-1003", "item arrived damaged", "My Orion X2 arrived with a cracked case."),
    ("LM-1004", "address could not be verified", "Why has my order not shipped?"),
]
sent = 0
for order_id, reason, question in CASES:
    payload = escalation_payload(order_id, reason, question)
    line = escalate(order_id, reason, question)
    ok = line.startswith("Escalated as")
    sent += ok
    print("Case:", question)
    print("   payload :", json.dumps(payload))
    print("   result  :", line)
    print()

print("RESULT CHECK 1: %d of %d cases were escalated." % (sent, len(CASES)))
print("RESULT CHECK 2: the payload carries %d field(s) (3 is right: order_id, reason, question)."
      % len(escalation_payload("LM-1", "r", "q")))
print("RESULT CHECK 3: the failure rule is %s." % ("written" if len(FAILURE_RULE) > 40 else "EMPTY - TODO 3"))
print()

# Deliberately break it, and see that the agent is told the truth.
print("Now the same call to a url that does not exist - this is the case that matters:")
broken = post_to_n8n(escalation_payload("LM-1003", "damaged", "test"),
                     url="https://example.invalid/webhook/escalate", timeout=3)
print("   ", broken.get("error", broken))
print("RESULT CHECK 4: a broken escalation returns a message, not a crash: %s"
      % ("YES" if broken.get("ok") is False else "NO"))
if not N8N_URL:
    print()
    print("NOTE: N8N_WEBHOOK_URL is not set, so a local stand-in answered. Your Python is right, but your")
    print("      WORKFLOW is not proven. Put the production url in .env and run this again.")
