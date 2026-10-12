"""Offline tests for the project kit: a scripted fake LLM, no keys, no network.
Run:  python tests/test_kit.py
"""
import sys, os, json, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "example_support_desk"))
from utils.llm_client import ChatResult, ToolCall
import project as P
from kit_agent import ProjectAgent, Budget
from kit_planner import run_plan, parse_plan, check_plan
from kit_reflect import reflect
from kit_eval import run_eval

_n = [0]
def call(name, **args):
    _n[0] += 1
    return ToolCall(f"c{_n[0]}", name, args)

def say(text):                   return ChatResult(text, [], {"role": "assistant", "content": text})
def use(thought, *calls):        return ChatResult(thought, list(calls), {"role": "assistant", "content": thought})

class FakeClient:
    """chat(): pops scripted ChatResults.  get_completion(): pops scripted strings."""
    def __init__(self, chats=(), completions=()):
        self.chats, self.completions = list(chats), list(completions)
    def chat(self, messages, tools=None, **kw):
        return self.chats.pop(0)
    def get_completion(self, prompt, **kw):
        return self.completions.pop(0)

def test_react_and_report():
    c = FakeClient([use("I need the order.", call("get_order_status", order_id="A100")),
                    say("Order A100 is shipped.")])
    a = P.make_agent(client=c)
    ans = a.run("What is the status of order A100?")
    assert "shipped" in ans and a.report["stop_reason"] == "goal_reached"
    assert a.report["steps"] == 2 and a.report["tool_calls"] == 1 and a.trace[0]["action"] == "get_order_status"

def test_repeat_guard_warns_then_stops():
    same = lambda: use("again", call("check_stock", sku="K10"))
    c = FakeClient([same(), same(), same(), say("never reached")])
    a = P.make_agent(client=c)
    a.run("loop")
    assert a.report["stop_reason"] == "repeat_guard"
    assert a.trace[1]["observation"].startswith("error: you already made this exact call")

def test_step_and_tool_budget():
    c = FakeClient([use("x", call("check_stock", sku=s)) for s in ("K10", "M20", "K10", "M20")])
    a = P.make_agent(client=c, budget=Budget(max_steps=2))
    a.run("x");  assert a.report["stop_reason"] == "step_budget"
    c = FakeClient([use("x", call("check_stock", sku="K10"), call("check_stock", sku="M20"))])
    a = P.make_agent(client=c, budget=Budget(max_tool_calls=1))
    a.run("x");  assert a.report["stop_reason"] == "tool_budget"

def test_approval_gate():
    refund = lambda: [use("refund", call("issue_refund", order_id="A101", amount=90)), say("done")]
    a = P.make_agent(client=FakeClient(refund()), approve=None)          # auto-deny
    a.run("refund"); assert a.trace[0]["observation"].startswith("error: a human did not approve")
    a = P.make_agent(client=FakeClient(refund()), approve=lambda n, args: True)
    a.run("refund"); assert a.trace[0]["observation"].startswith("refund of 90")

def test_tool_never_raises():
    c = FakeClient([use("bad", call("get_order_status", wrong_arg=1)), say("sorry")])
    a = P.make_agent(client=c); a.run("x")
    assert a.trace[0]["observation"].startswith("error:")

def test_planner_json_and_replan():
    assert [s["tool"] for s in parse_plan('noise {"steps":[{"id":1,"task":"a","tool":"find_customer"}]} end')] == ["find_customer"]
    assert parse_plan("1. first\n2. second")[1]["task"] == "second"
    plan1 = '{"steps":[{"id":1,"task":"Find customer","tool":"find_customer"},{"id":2,"task":"Get orders","tool":"get_orders"}]}'
    plan2 = '{"steps":[{"id":1,"task":"Look up order A101","tool":"get_order_status"}]}'
    chats = [use("", call("find_customer", email="nobody@x.com")), say("could not find the customer"),   # step 1 FAILS
             use("", call("get_order_status", order_id="A101")), say("A101 is delayed")]                  # replanned step
    c = FakeClient(chats, completions=[plan1, plan2, "Order A101 is delayed."])
    a = P.make_agent(client=c)
    out = run_plan(a, "x", verbose=False)
    assert out["replans"] == 1 and "delayed" in out["answer"], out
    bad = parse_plan('{"steps":[{"id":1,"task":"t","tool":"teleport"}]}')
    assert check_plan(bad, a) and not check_plan(parse_plan(plan1), a)

def test_plan_rejected_by_human():
    c = FakeClient(completions=['{"steps":[{"id":1,"task":"x","tool":null}]}'])
    out = run_plan(P.make_agent(client=c), "x", approve_plan=lambda p: False, verbose=False)
    assert out["status"] == "plan_rejected"

def test_reflection_revise_then_confirm():
    chats = [use("", call("find_customer", email="omar@example.com")),
             use("", call("create_ticket", customer_id="C-310", issue="late")),
             say("I opened a ticket for you."),                                  # missing the ticket number
             say("Ticket T-1001 created for C-310.")]                            # revised
    def verifier(ans, ag):
        used = [s["action"] for s in ag.trace if s["action"]]
        return [] if "create_ticket" not in used or "T-" in ans else ["answer lacks ticket number"]
    c = FakeClient(chats, completions=[json.dumps({"verdict": "CONFIRM", "issues": []})])
    a = P.make_agent(client=c)
    out = reflect(a, "ticket please", rubric=["states the ticket id"], verifier=verifier, budget=2, verbose=False)
    assert out["status"] == "confirmed" and out["rounds"] == 1 and "T-1001" in out["answer"], out

def test_reflection_budget_exhausted_is_flagged():
    c = FakeClient([say("a1"), say("a2"), say("a3")],
                   completions=[json.dumps({"verdict": "REVISE", "issues": ["bad"]})] * 2)
    out = reflect(P.make_agent(client=c), "g", rubric=["r"], budget=2, verbose=False)
    assert out["status"] == "unverified" and out["rounds"] == 2

def test_reflection_needs_input_is_not_revised():
    c = FakeClient([say("Which email address should I use?")])      # no tools, ends with '?'
    out = reflect(P.make_agent(client=c), "find my orders", rubric=["r"], budget=2, verbose=False)
    assert out["status"] == "needs_input" and out["rounds"] == 0      # critic never called (would pop an empty list)

def test_eval_harness():
    tasks = [{"id": "T1", "type": "easy", "goal": "status A100", "must_call": ["get_order_status"],
              "answer_contains": ["shipped"], "max_steps": 3},
             {"id": "T2", "type": "easy", "goal": "status A100", "must_call": ["create_ticket"]}]
    path = os.path.join(tempfile.mkdtemp(), "g.json"); json.dump(tasks, open(path, "w"))
    scripts = iter([FakeClient([use("", call("get_order_status", order_id="A100")), say("A100 is shipped")]),
                    FakeClient([say("no idea")])])
    s = run_eval(lambda: P.make_agent(client=next(scripts)), tasks_path=path,
                 out=os.path.join(tempfile.mkdtemp(), "r.json"), quiet=True)
    assert s["passed"] == 1 and s["total"] == 2

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t(); print("PASS", t.__name__)
    print(f"\nall {len(tests)} kit tests passed")
