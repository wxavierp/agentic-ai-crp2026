"""Checks that every mechanism script runs key-free and every planted bug shows its symptom
(and that the one-line fix removes it).   python project_kit/tests/test_mechanisms.py"""
import os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "mechanisms"))


def run(path, text_patch=None):
    src = open(path).read()
    if text_patch:
        old, new = text_patch
        assert old in src, f"bug line not found in {path}: {old}"
        src = src.replace(old, new)
    return subprocess.run([sys.executable, "-I", "-c", src], capture_output=True, text=True,
                          cwd=ROOT, timeout=30).stdout


def test_naked_scripts_run():
    for f in ["m1_reflect_naked.py", "m2_guards_naked.py", "m3_injection_naked.py", "m4_eval_table.py"]:
        r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, f)], capture_output=True,
                           text=True, cwd=ROOT, timeout=30)
        assert r.returncode == 0 and r.stdout.strip(), f


BUGS = {  # file: (symptom text in buggy output, (bug, fix), text expected after fix)
    "bug_A_repeat_guard.py": ("repeat_guard", ("key = name  ", "key = (name, tuple(args.items()))  "), "goal_reached"),
    "bug_B_verifier.py": ("none -> status CONFIRMED", (r'r"T-\d"', r'r"T-\d+"'), "T-1001 was never returned"),
    "bug_C_approval_gate.py": ("REFUNDED 40", ('{"refund",', '{"issue_refund",'), "side effects: none"),
    "bug_D_budget.py": ("tools that actually ran: 4", ("tool_calls > max_tool_calls", "tool_calls >= max_tool_calls"), "tools that actually ran: 3"),
    "bug_E_eval_check.py": ("result : PASS", ('for t in task["must_not_call"]:\n        if t not in', 'for t in task["must_not_call"]:\n        if t in'), "FAIL"),
}


def test_bug_symptoms_and_fixes():
    for f, (symptom, patch, after) in BUGS.items():
        path = os.path.join(ROOT, "bughunt", f)
        assert symptom in run(path), f"{f}: symptom missing"
        out = run(path, patch)
        assert after in out, f"{f}: fix did not work -> {out}"


def _drive(args, answers, cwd):
    return subprocess.run([sys.executable, os.path.join(ROOT, "run_mechanism.py"), *args], input="\n".join(answers) + "\n",
                          capture_output=True, text=True, cwd=cwd, timeout=60).stdout


def test_run_mechanism_flow():
    import tempfile, json, base64
    tmp = tempfile.mkdtemp()
    assert "READY" in _drive(["check"], ["17"], tmp)
    out = _drive(["m1", "try"], ["none", "blind", "unverified"], tmp);   assert "SCORE 3/3" in out
    out = _drive(["m2", "try"], ["2 step_budget", "4 tool_budget", "7 repeat_guard"], tmp);   assert "SCORE 3/3" in out
    out = _drive(["m2", "try"], ["9 tool", "9 tool", "9 tool"], tmp);   assert "SCORE 0/3" in out      # wrong answers are scored wrong
    out = _drive(["m3", "try"], ["yes", "yes", "no"], tmp);   assert "SCORE 3/3" in out
    out = _drive(["m4", "try"], ["3.75", "G5", "ship C: best pass rate and refunds are risky"], tmp);   assert "SCORE 2/2" in out
    # empty answers are asked again (cannot skip)
    out = _drive(["m1", "try"], ["", "none", "blind", "unverified"], tmp);   assert "an answer is needed" in out
    _drive(["bug"], ["21", "because", "fix"], tmp); _drive(["bug"], ["21", "because", "fix", "nothing"], tmp)
    line = _drive(["receipt"], [], tmp).split("\n")
    rec = next(l for l in line if l.startswith("D10."))
    body = rec.split(".")[1]; data = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    assert data["id"] == 17 and data["bug"] == "C" and data["res"]["m3"] == "3/3" and data["p1"] == 21
    # prediction is logged before the result
    kinds = [json.loads(l)["kind"] for l in open(os.path.join(tmp, "predictions.jsonl"))]
    assert kinds.index("prediction") < kinds.index("result")


if __name__ == "__main__":
    test_naked_scripts_run(); print("naked scripts OK")
    test_bug_symptoms_and_fixes(); print("bug hunt symptoms + fixes OK")
    test_run_mechanism_flow(); print("run_mechanism flow OK")
