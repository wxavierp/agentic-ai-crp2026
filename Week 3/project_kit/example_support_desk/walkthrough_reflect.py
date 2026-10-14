"""Day 10 live walkthrough - ONE reflection round on the REAL agent, every hand-off printed.

The kit's own reflect() runs unchanged. This script only adds print statements around it, so you can see
exactly what goes where:

    STEP 1  GENERATE  agent.run(goal)             -> trace   (what the agent did)
    STEP 2  EVIDENCE  agent.evidence()            -> the list the critic will be shown
    STEP 3  VERIFY    your verifier(answer, agent) -> problems found by CODE
    STEP 4  CRITIQUE  the prompt text sent to the critic model, and its JSON reply
    STEP 5  REVISE    agent.run(...) again with the problems fed back
    ...then CONFIRM (status confirmed) or flag (unverified)

A model rarely makes a mistake on cue, so by default the script PLANTS one: it edits the first answer
(reverses a number) and says so on screen. Everything after that - the verifier, the critic, the revision -
is real.

Run:   python example_support_desk/walkthrough_reflect.py              real model (needs a key in .env)
       python example_support_desk/walkthrough_reflect.py --offline    scripted, no key, same output shape
       python example_support_desk/walkthrough_reflect.py --no-plant   a clean run: the critic confirms
Note:  the goal is read-only on purpose. A revision RUNS THE AGENT AGAIN, so a tool with side effects
       (create_ticket, issue_refund) would run twice. See the 'gotcha' on the Day 10 slides.
"""
import sys, os, re, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
sys.path.append(HERE)
from project import make_agent
from kit_reflect import reflect
from utils.llm_client import ChatResult, ToolCall

GOAL = "What is the total of order A100, and is its sku in stock? Answer in one short sentence."
RUBRIC = [
    "Answers what the user asked",
    "Every number and id in the answer appears in the EVIDENCE (tool results)",
]


def banner(n, title, where):
    print(f"\n{'=' * 72}\nSTEP {n}  {title}    [{where}]\n{'=' * 72}")


def verifier(answer, agent):
    """CODE check: every number in the answer must appear somewhere in the tool results."""
    seen = " ".join(agent.evidence())
    return [f"the number {n} is in the answer but in no tool result"
            for n in re.findall(r"\d+", answer or "") if n not in seen]


def plant_mistake(answer):
    """Swap the first two digits of the first 2+ digit number: 240 -> 420 (a plausible slip)."""
    m = re.search(r"\b(\d{2,})\b", answer or "")
    if not m:
        return (answer or "") + " (total 999 AED)"
    d = list(m.group(1))
    d[0], d[1] = d[1], d[0]
    bad = "".join(d)
    if bad == m.group(1):
        bad = str(int(m.group(1)) + 7)
    return answer[:m.start()] + bad + answer[m.end():]


class ScriptedClient:
    """Offline stand-in for the model: two scripted agent runs and one critic reply."""
    def __init__(self):
        n = [0]
        def call(name, **a):
            n[0] += 1
            return ToolCall(f"s{n[0]}", name, a)
        def use(t, c): return ChatResult(t, [c], {"role": "assistant", "content": t})
        def say(t):    return ChatResult(t, [], {"role": "assistant", "content": t})
        run = lambda: [use("I need the order total and its sku.", call("get_order_status", order_id="A100")),
                       use("The sku is K10 - checking stock.", call("check_stock", sku="K10")),
                       say("Order A100 totals 240 AED and its sku K10 has 0 units in stock.")]
        self.chats = run() + run()
        self.completions = ['{"verdict": "CONFIRM", "issues": []}']
        self.provider = "scripted"
    def chat(self, messages, tools=None, **kw):
        return self.chats.pop(0)
    def get_completion(self, prompt, **kw):
        return self.completions.pop(0)
    def _default_model(self):
        return "scripted-offline"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="scripted model, no key needed")
    ap.add_argument("--no-plant", action="store_true", help="do not plant a mistake")
    a = ap.parse_args(argv)

    client = ScriptedClient() if a.offline else None
    agent = make_agent(approve=None, client=client)
    model = f"{agent.client.provider} / {agent.client._default_model()}" if hasattr(agent.client, "_default_model") else "?"
    print(f"GOAL : {GOAL}\nMODEL: {model}" + ("   (OFFLINE SCRIPT - no real model)" if a.offline else ""))

    state = {"runs": 0}
    real_run = agent.run

    def run(prompt):
        state["runs"] += 1
        if state["runs"] == 1:
            banner(1, "GENERATE - the agent works", "agent.run(goal)")
        else:
            banner(5, "REVISE - the agent runs AGAIN, now told what was wrong", "agent.run(goal + problems)")
            print("(fresh run: its tools run again - fine for lookups, a duplicate for create_ticket / refund)")
        ans = real_run(prompt)
        agent.print_trace()
        banner(2, "EVIDENCE" + (" (again, from the NEW run)" if state["runs"] > 1 else "") + " - what the critic and the verifier will be shown", "agent.evidence()")
        for i, line in enumerate(agent.evidence(), 1):
            print(f" {i}. {line}")
        print(f"\nANSWER FROM THE MODEL: {ans}")
        if state["runs"] == 1 and not a.no_plant:
            bad = plant_mistake(ans)
            print(f"\n*** PLANTED MISTAKE (we edit the answer on purpose, the rest is real) ***\nANSWER NOW: {bad}")
            return bad
        return ans
    agent.run = run

    def verify(answer, ag):
        banner(3, "VERIFY" + (" (again)" if state["runs"] > 1 else "") + " - your code checks the answer against the evidence", "verifier(answer, agent)")
        problems = verifier(answer, ag)
        print("problems found by code:", problems if problems else "none")
        return problems

    real_completion = agent.client.get_completion
    def spy(prompt, *args, **kw):
        banner(4, "CRITIQUE - this exact text is sent to the critic model", "kit_reflect.critique()")
        print(prompt)
        out = real_completion(prompt, *args, **kw)
        print(f"\nCRITIC REPLIED: {out}")
        return out
    agent.client.get_completion = spy

    out = reflect(agent, GOAL, RUBRIC, verifier=verify, budget=2, verbose=True)
    print(f"\n{'=' * 72}\nRESULT\n{'=' * 72}")
    print("FINAL :", out["answer"])
    print("STATUS:", out["status"], "| revise rounds:", out["rounds"])
    print("ISSUES FOUND ALONG THE WAY:", out["issues"])
    return out


if __name__ == "__main__":
    main()
