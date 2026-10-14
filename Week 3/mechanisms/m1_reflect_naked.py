"""
Mechanism 1 - WHY a critic must see the evidence, and why code beats opinion.
No API key. Run:  python mechanisms/m1_reflect_naked.py

PREDICT FIRST (write it down before running):
  The agent's answer is WRONG (see below). Which of the three reviewers will catch it?
      blind critic / grounded critic / code verifier      -> catch or miss?
"""
import re

# ---- the situation -----------------------------------------------------------------
EVIDENCE = "create_ticket(customer_id='C-310') -> 'T-1002 created'"     # what the tool REALLY returned
ANSWER   = "Ticket T-1001 has been created for Omar."                   # what the agent CLAIMS


def _id(text):
    return re.search(r"T-\d+", text).group()


# ---- three ways to review it ---------------------------------------------------------
def critic_blind(answer):
    """SIMULATED model critic that only reads the answer's wording (no tool results)."""
    sounds_fine = answer.endswith(".") and "Ticket" in answer
    return [] if sounds_fine else ["answer looks incomplete"]


def critic_grounded(answer, evidence):
    """SIMULATED model critic that is shown the tool results."""
    return [] if _id(answer) == _id(evidence) else ["ticket id differs from the tool result"]


def verifier_code(answer, evidence):
    """Plain python. No model. Deterministic, instant, free."""
    return [] if _id(answer) == _id(evidence) else ["ticket id in answer != id from the tool"]


print("ANSWER  :", ANSWER)
print("EVIDENCE:", EVIDENCE, "\n")
for name, problems in [("blind critic   ", critic_blind(ANSWER)),
                       ("grounded critic", critic_grounded(ANSWER, EVIDENCE)),
                       ("code verifier  ", verifier_code(ANSWER, EVIDENCE))]:
    print(f"{name}: {'CAUGHT -> ' + problems[0] if problems else 'MISSED (confirmed a wrong answer)'}")


# ---- part 2: the reflection loop and its BUDGET ---------------------------------------
def reflect(generate, review, budget):
    answer = generate(None)                                   # GENERATE
    for rnd in range(1, budget + 1):
        problems = review(answer)                             # REVIEW
        if not problems:
            return answer, "confirmed", rnd - 1
        answer = generate(problems)                           # REVISE using the feedback
    return answer, "unverified", budget                       # budget spent: FLAG, never ship silently


def fixable(feedback):                       # a generator that fixes it once it hears the problem
    return "Ticket T-1002 has been created for Omar." if feedback else ANSWER


def stubborn(feedback):                      # a generator that ignores feedback
    return ANSWER


print("\n--- the loop (verifier = code check) ---")
review = lambda a: verifier_code(a, EVIDENCE)
for label, gen, budget in [("fixable generator, budget 2", fixable, 2),
                           ("stubborn generator, budget 2", stubborn, 2),
                           ("stubborn generator, budget 5", stubborn, 5)]:
    answer, status, rounds = reflect(gen, review, budget)
    print(f"{label:30s} -> status={status:10s} revise-rounds={rounds}")
print("\nQUESTION: why is 'unverified' a better outcome than silently returning the answer?")
