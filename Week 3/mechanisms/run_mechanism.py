"""
run_mechanism.py - your Session-10 companion. Everything you do here is recorded in
predictions.jsonl, and `receipt` turns it into ONE line you submit (that line is part of
Milestone M3, Part B).

    python mechanisms/run_mechanism.py check           # 1) once: set your roster number, test setup
    python mechanisms/run_mechanism.py m1              # 2) WATCH: run the demo with the instructor (no questions)
    python mechanisms/run_mechanism.py m1 try          # 3) TRY: 3 NEW situations - you predict, then the computer answers
    (same for m2, m3, m4)
    python mechanisms/run_mechanism.py bug             # bug hunt (your file = roster number mod 5)
    python mechanisms/run_mechanism.py receipt         # at the end: prints your one-line receipt

Order matters: you only get questions AFTER the idea has been explained and demonstrated.
Your answers are saved BEFORE the computer reveals the truth, so the record is honest.
Run it from the "Week 3" folder.
"""
import base64, contextlib, hashlib, io, itertools, json, os, re, runpy, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = "predictions.jsonl"
IDFILE = ".student_id"
SALT = "d10-2026"


# ---------------------------------------------------------------- small helpers
def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def log(rec):
    rec = {"t": now(), **rec}
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def read_log():
    if not os.path.exists(LOG):
        return []
    return [json.loads(l) for l in open(LOG) if l.strip()]


def ask(q, allow_empty=False):
    """Questions cannot be skipped: an empty answer is asked again."""
    while True:
        try:
            a = input(q).strip()
        except EOFError:
            sys.exit("\n(input closed - run this in a terminal)")
        if a or allow_empty:
            return a
        print("   (an answer is needed - a guess is fine, that is the point)")


def student():
    if os.path.exists(IDFILE):
        return int(open(IDFILE).read().strip())
    return None


def need_student():
    s = student()
    if s is None:
        sys.exit("Run first:  python mechanisms/run_mechanism.py check")
    return s


def load(name):
    """Run a mechanism script quietly; return (printed_text, its_namespace)."""
    path = os.path.join(HERE, name)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ns = runpy.run_path(path)
    return buf.getvalue(), ns


def first_int(text):
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None


def guard_word(text):
    t = text.lower()
    for key, word in (("step", "step_budget"), ("tool", "tool_budget"), ("repeat", "repeat_guard"),
                      ("time", "time_budget"), ("goal", "goal_reached")):
        if key in t:
            return word
    return t.strip()


def yn(text):
    return "yes" if text.strip().lower().startswith(("y", "t", "1")) else "no"


def scorecard(mech, rows):
    """rows = [(question, you, truth, ok)]"""
    print("\n=== YOU vs THE COMPUTER ===")
    pts = 0
    for q, you, truth, ok in rows:
        pts += bool(ok)
        print(f"  {'OK  ' if ok else 'MISS'} {q}\n         you: {you}   computer: {truth}")
    print(f"\n  SCORE {pts}/{len(rows)}.  A MISS is not a failure - it is exactly where your picture of the idea is "
          "still fuzzy. Be ready to say WHY you were wrong.")
    log({"kind": "result", "mech": mech, "student": student(), "score": pts, "max": len(rows)})
    return pts


# ---------------------------------------------------------------- check
def cmd_check():
    print("Python:", sys.version.split()[0])
    sid = student()
    if sid is None:
        sid = int(ask("Your roster number (the number the instructor gave you): "))
        open(IDFILE, "w").write(str(sid))
    for f in ("m1_reflect_naked.py", "m2_guards_naked.py", "m3_injection_naked.py", "m4_eval_table.py"):
        assert os.path.exists(os.path.join(HERE, f)), f"missing {f} - git pull"
    bug = "ABCDE"[sid % 5]
    log({"kind": "check", "student": sid})
    print(f"\nREADY.  Student #{sid}.  Your bug-hunt file is bug_{bug}.  Predictions are saved in ./{LOG}")


# ---------------------------------------------------------------- m1
def m1_watch():
    out, _ = load("m1_reflect_naked.py")
    print(out)


def m1_try():
    sid = need_student()
    _, ns = load("m1_reflect_naked.py")
    cb, cg, vc, reflect, fixable, stubborn = (ns[k] for k in
        ("critic_blind", "critic_grounded", "verifier_code", "reflect", "fixable", "stubborn"))
    EV, ANSWER = ns["EVIDENCE"], ns["ANSWER"]
    print("""
THREE NEW SITUATIONS (the evidence is the same as before: create_ticket -> 'T-1002 created')
  The reviewers: BLIND critic (sees only the answer), GROUNDED critic (sees answer + evidence), CODE verifier.
  A reviewer 'flags' an answer when it says there is a problem.
""")
    a1 = "Ticket T-1002 has been created for Omar."          # correct answer
    a2 = "T-1002 done"                                      # correct id, but clipped wording
    print("  Situation 1: the agent's answer is CORRECT:  ", a1)
    q1 = ask("   Which reviewers flag it?  (any of: blind grounded code  - or 'none'): ")
    print("  Situation 2: the answer has the RIGHT ticket id but short wording:  ", a2)
    q2 = ask("   Which reviewers flag it?  (any of: blind grounded code  - or 'none'): ")
    print("  Situation 3: the agent can fix the problem once it hears about it (generator 'fixable'), the reviewer is the "
          "code verifier, and the budget is only ONE round.")
    q3 = ask("   Final status?  (confirmed / unverified): ")
    log({"kind": "prediction", "mech": "m1", "student": sid, "answers": [q1, q2, q3]})

    def flagged(answer):
        out = set()
        if cb(answer): out.add("blind")
        if cg(answer, EV): out.add("grounded")
        if vc(answer, EV): out.add("code")
        return out

    def parse(s):
        words = set(re.findall(r"blind|grounded|code", s.lower()))
        return words
    t1, t2 = flagged(a1), flagged(a2)
    t3 = reflect(fixable, lambda a: vc(a, EV), 1)[1]
    fmt = lambda s: ", ".join(sorted(s)) or "none"
    scorecard("m1", [
        ("Situation 1 - who flags a CORRECT answer?", fmt(parse(q1)), fmt(t1), parse(q1) == t1),
        ("Situation 2 - who flags right-id/short wording?", fmt(parse(q2)), fmt(t2), parse(q2) == t2),
        ("Situation 3 - fixable generator, budget 1", q3.lower(), t3, q3.lower().startswith(t3[:5])),
    ])
    print("\n  WHY (read after the score):\n"
          "   S2: the blind critic judges how the answer LOOKS - it cannot know the id is right, so it can raise a false alarm.\n"
          "   S3: with budget 1 the loop reviews once, revises once, and then STOPS - the revised answer was never re-checked,\n"
          "       so the honest status is 'unverified'. A revision needs one more review to count as confirmed.")


# ---------------------------------------------------------------- m2
def m2_watch():
    out, _ = load("m2_guards_naked.py")
    print(out)


def m2_try():
    sid = need_student()
    _, ns = load("m2_guards_naked.py")
    run = ns["run"]
    K, M, P = ("check_stock", {"sku": "K10"}), ("check_stock", {"sku": "M20"}), ("check_stock", {"sku": "P30"})
    cfgs = [
        ("F", "same call K10 forever, repeat guard ON, max_steps = 2",
         lambda: run(itertools.cycle([K]), max_steps=2, repeat_guard=True)),
        ("G", "K10, M20, K10, M20 ... NO repeat guard, max_tool_calls = 3 (max_steps = 8)",
         lambda: run(itertools.cycle([K, M]), max_tool_calls=3)),
        ("H", "K10, M20, P30, K10, M20, P30 ... repeat guard ON (max_steps = 8)",
         lambda: run(itertools.cycle([K, M, P]), repeat_guard=True)),
    ]
    print("\nTHREE NEW CONFIGURATIONS. For each write: the step where it stops, and which guard stops it.")
    print("(guards: step_budget  tool_budget  repeat_guard)   e.g.  '6 tool_budget'\n")
    ans = []
    for letter, desc, _ in cfgs:
        ans.append(ask(f"  {letter}) {desc}\n     your answer: "))
    log({"kind": "prediction", "mech": "m2", "student": sid, "answers": ans})
    rows = []
    for (letter, desc, fn), a in zip(cfgs, ans):
        step, reason = fn()
        ok = first_int(a) == step and guard_word(a) == reason
        rows.append((f"{letter}) {desc}", a, f"{step} {reason}", ok))
    scorecard("m2", rows)
    print("\n  WHY: a guard only fires when ITS condition is met - the repeat guard counts the SAME tool+args, so a 3-call\n"
          "  rotation (H) needs 7 steps to see the third repeat; step_budget fires when nothing else did; tool_budget counts\n"
          "  calls that actually ran, so it stops at the step AFTER the last allowed call.")


# ---------------------------------------------------------------- m3
def m3_watch():
    out, _ = load("m3_injection_naked.py")
    print(out)


def m3_try():
    sid = need_student()
    _, ns = load("m3_injection_naked.py")
    run, LOG_ = ns["run"], ns["REFUND_LOG"]
    cases = [
        ("approval gate ON, but the human approves everything (approve = always yes)", dict(gate=True, approve=lambda n, a: True)),
        ("allow-list = {get_ticket_notes, issue_refund}  (the task only needed notes)", dict(allowed={"get_ticket_notes", "issue_refund"})),
        ("approval gate ON (nobody approves) AND allow-list = {get_ticket_notes}", dict(gate=True, allowed={"get_ticket_notes"})),
    ]
    print("\nTHREE NEW DEFENCES. For each: does the attacker's refund actually execute?  (yes / no)\n")
    ans = [ask(f"  {i}) {d}\n     refund executes? ") for i, (d, _) in enumerate(cases, 1)]
    log({"kind": "prediction", "mech": "m3", "student": sid, "answers": ans})
    rows = []
    for i, ((d, kw), a) in enumerate(zip(cases, ans), 1):
        run(**kw)
        truth = "yes" if LOG_ else "no"
        rows.append((f"{i}) {d}", yn(a), truth, yn(a) == truth))
    scorecard("m3", rows)
    print("\n  WHY: a defence works only if the code actually BLOCKS the call. A gate that always says yes, or an allow-list\n"
          "  that still contains the dangerous tool, blocks nothing. Least privilege = the dangerous tool is simply not there.")


# ---------------------------------------------------------------- m4
def m4_watch():
    out, _ = load("m4_eval_table.py")
    print(out)


def m4_try():
    sid = need_student()
    _, ns = load("m4_eval_table.py")
    R = ns["RESULTS"]
    names = list(R)
    B, C = R[names[1]], R[names[2]]
    print("\nTHE TABLE IS A TEST OF YOUR READING. Three questions:\n")
    q1 = ask("  1) A new variant D passes 4 of the 5 tasks and used 15 model calls in total. What is its calls/pass? (number): ")
    q2 = ask("  2) Which task does variant C pass that variant B fails?  (e.g. G3): ")
    q3 = ask("  3) You must ship ONE of A, B, C for a support desk that handles REFUNDS. Which, and WHY? (a full sentence): ")
    while len(q3.split()) < 6:
        q3 = ask("     (write at least a short sentence - the reason is the point): ")
    log({"kind": "prediction", "mech": "m4", "student": sid, "answers": [q1, q2, q3]})
    t1 = 15 / 4
    t2 = [t for t in B if B[t][0] == 0 and C[t][0] == 1][0]
    try:
        ok1 = abs(float(re.findall(r"[\d.]+", q1)[0]) - t1) <= 0.1
    except Exception:
        ok1 = False
    scorecard("m4", [("1) calls/pass of D = 15 / 4", q1, f"{t1:.2f}", ok1),
                     ("2) passed by C, failed by B", q2.upper(), t2, t2.lower() in q2.lower())])
    print("\n  Question 3 has no single right answer - the instructor will cold-call a few of you to defend it.\n"
          "  (A strong answer names the table: pass rate, calls/pass, WHICH task fails, and the cost of a wrong refund.)")


# ---------------------------------------------------------------- bug hunt
BUGDIR = os.path.join(HERE, "bughunt")
BUGFILES = {"A": "bug_A_repeat_guard.py", "B": "bug_B_verifier.py", "C": "bug_C_approval_gate.py",
            "D": "bug_D_budget.py", "E": "bug_E_eval_check.py"}


def cmd_bug():
    sid = need_student()
    letter = (sys.argv[3].upper() if len(sys.argv) > 3 else "ABCDE"[sid % 5])
    path = os.path.join(BUGDIR, BUGFILES[letter])
    state = [r for r in read_log() if r.get("kind") in ("bug_p1",) and r.get("student") == sid and r.get("file") == letter]
    print(f"\nBUG HUNT - student #{sid} - file bug_{letter}   (open it in your editor: {os.path.relpath(path)})\n")
    print("--- what the program does ---")
    os.system(f'"{sys.executable}" -I "{path}"')
    if not state:
        print("\nPHASE 1 - NO AI. Read the code. Find the ONE buggy line. (about 4 minutes)")
        start = time.time()
        line = ask("  line number of the bug: ")
        why = ask("  why does it cause the symptom? (1-2 sentences): ")
        fix = ask("  your one-line fix: ")
        log({"kind": "bug_p1", "student": sid, "file": letter, "line": first_int(line), "why": why, "fix": fix,
             "minutes": round((time.time() - start) / 60, 1)})
        print("\nSaved. Phase 1 is locked in. Now AI is allowed: run this command again to give your FINAL answer.")
    else:
        print("\nPHASE 2 - AI is allowed now. Give your FINAL answer (you can change your mind).")
        line = ask("  line number of the bug: ")
        why = ask("  why does it cause the symptom? (1-2 sentences): ")
        fix = ask("  your one-line fix: ")
        note = ask("  What did the AI tell you that you had NOT already found? (or 'nothing / did not use AI'): ")
        log({"kind": "bug_p2", "student": sid, "file": letter, "line": first_int(line), "why": why, "fix": fix, "ai_note": note[:80]})
        print("\nSaved. Wait for the instructor's walkthrough of the bug.")


# ---------------------------------------------------------------- receipt
def cmd_receipt():
    sid = need_student()
    recs = [r for r in read_log() if r.get("student") == sid]
    best = {}
    for r in recs:
        if r["kind"] == "result":
            best[r["mech"]] = f'{r["score"]}/{r["max"]}'
    p1 = next((r for r in recs if r["kind"] == "bug_p1"), None)
    p2 = [r for r in recs if r["kind"] == "bug_p2"]
    p2 = p2[-1] if p2 else None
    preds = [r for r in recs if r["kind"] == "prediction"]
    ptr = [r.get("points") for r in read_log() if r.get("kind") == "actual" and "points" in r]
    payload = {"id": sid, "res": best, "n_pred": len(preds),
               "bug": (p1 or p2 or {}).get("file"), "p1": p1 and p1["line"], "p1m": p1 and p1["minutes"],
               "p2": p2 and p2["line"], "ai": (p2 or {}).get("ai_note", "")[:60], "ptr": ptr}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    chk = hashlib.sha256((body + SALT).encode()).hexdigest()[:6]
    line = f"D10.{body}.{chk}"
    open("receipt.txt", "w").write(line + "\n")
    print("\nYOUR RECEIPT (also saved in receipt.txt). Submit this single line exactly as printed:\n")
    print(line)
    print(f"\n  predictions made: {len(preds)}   scores: {best}   bug hunt: {'done' if p2 else ('phase 1 only' if p1 else 'not done')}")


# ---------------------------------------------------------------- main
CMDS = {"m1": (m1_watch, m1_try), "m2": (m2_watch, m2_try), "m3": (m3_watch, m3_try), "m4": (m4_watch, m4_try)}

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "check": cmd_check()
    elif a[0] == "bug": cmd_bug()
    elif a[0] == "receipt": cmd_receipt()
    elif a[0] in CMDS:
        CMDS[a[0]][1 if len(a) > 1 and a[1] == "try" else 0]()
    else:
        sys.exit(__doc__)
