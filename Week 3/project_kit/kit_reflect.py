"""
kit_reflect.py — add REFLECTION to any agent (Day 10).

    generate -> VERIFY (code checks) -> CRITIQUE (rubric + evidence) -> revise -> confirm

Two ideas that matter in 2026:
  1. Verify with CODE first. A python check ("did it call create_ticket?",
     "is the number in the answer equal to the tool result?") is cheaper and more
     reliable than asking a model for its opinion.
  2. A critic must SEE THE EVIDENCE (the tool results), and judge against a RUBRIC
     you wrote down - not "is this good?".

    from kit_reflect import reflect
    out = reflect(agent, goal, rubric=["States the order status from the tool",
                                      "Gives the customer a next step"],
                  verifier=my_checks, budget=2)
"""

import json, re

CRITIC_PROMPT = """You are a strict reviewer. Judge the ANSWER against the RUBRIC, using
ONLY the EVIDENCE (tool results). Do not trust claims that the evidence does not support.

TASK: {goal}

EVIDENCE (what the tools actually returned):
{evidence}

ANSWER:
{answer}

RUBRIC (every line must hold):
{rubric}

Reply with ONLY this JSON:
{{"verdict": "CONFIRM" or "REVISE", "issues": ["one short sentence per failed rubric line"]}}"""


def critique(agent, goal, answer, rubric, evidence):
    prompt = CRITIC_PROMPT.format(
        goal=goal, answer=answer,
        evidence="\n".join(evidence) if evidence else "(no tools were called)",
        rubric="\n".join(f"- {r}" for r in rubric))
    text = agent.client.get_completion(prompt, temperature=0.0, max_tokens=250) or ""
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            verdict = str(d.get("verdict", "CONFIRM")).upper()
            return ("CONFIRM" if verdict.startswith("CONFIRM") else "REVISE"), list(d.get("issues", []))
        except ValueError:
            pass
    # Unparseable critic output: do not silently pass - treat as REVISE only if it says so.
    return ("REVISE", [text.strip()[:200]]) if "REVISE" in text.upper() else ("CONFIRM", [])


def asks_user(answer, agent):
    """True when the agent used no tools and its answer is a question back to the user."""
    used = [t for t in getattr(agent, "trace", []) if t.get("action")]
    return not used and str(answer or "").strip().endswith("?")


def reflect(agent, goal, rubric, verifier=None, budget=2, verbose=True):
    """
    verifier(answer, agent) -> list[str] of problems found by CODE ([] = fine). Optional.
    Returns {"answer","status","rounds","issues"}; status is:
      "confirmed"   - passed review
      "unverified"  - budget ran out with issues still open. NEVER ship that silently.
      "needs_input" - the agent asked the user a question instead of answering (nothing to
                      review yet - show the question and wait for the user's reply)
    """
    prompt, issues_log = goal, []
    answer = agent.run(prompt)
    if verbose:
        print(f"[generate] {answer}")
    if asks_user(answer, agent):
        return {"answer": answer, "status": "needs_input", "rounds": 0, "issues": []}

    for rnd in range(1, budget + 1):
        problems = list(verifier(answer, agent)) if verifier else []          # 1. code checks
        if not problems:                                                       # 2. LLM critic
            verdict, problems = critique(agent, goal, answer, rubric, agent.evidence())
        else:
            verdict = "REVISE"
        if verbose:
            print(f"[review {rnd}] {verdict}" + (f" - {problems}" if problems else ""))
        if verdict == "CONFIRM":
            return {"answer": answer, "status": "confirmed", "rounds": rnd - 1,
                    "issues": issues_log}
        issues_log.append(problems)
        prompt = (f"{goal}\n\nYour previous answer was rejected on review:\n- "
                  + "\n- ".join(problems) + "\nFix these points and give a corrected final answer.")
        answer = agent.run(prompt)                                             # 3. revise
        if verbose:
            print(f"[revise {rnd}] {answer}")

    return {"answer": answer, "status": "unverified", "rounds": budget, "issues": issues_log}
