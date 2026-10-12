"""
kit_eval.py — a mini evaluation harness: golden tasks in, pass-rate table out.

Your PROJECT_SPEC lists 5 golden tasks. Put them in golden_tasks.json and run:

    python kit_eval.py            (uses make_agent() from your project file)

Each task checks things you can verify WITHOUT a model:
    must_call        tools that have to appear in the trace
    must_not_call    tools that must NOT be called (e.g. a refund on a read-only task)
    answer_contains  strings the final answer must include (case-insensitive)
    max_steps        efficiency limit
This is Module 7 (Evaluation) in miniature - and it is how you prove your agent works.
"""

import json, time


def check_task(task, answer, agent):
    reasons = []
    used = [s["action"] for s in agent.trace if s["action"]]
    for t in task.get("must_call", []):
        if t not in used:
            reasons.append(f"did not call {t}")
    for t in task.get("must_not_call", []):
        if t in used:
            reasons.append(f"called forbidden tool {t}")
    for s in task.get("answer_contains", []):
        if s.lower() not in (answer or "").lower():
            reasons.append(f"answer missing '{s}'")
    if "max_steps" in task and agent.report.get("steps", 0) > task["max_steps"]:
        reasons.append(f"used {agent.report['steps']} steps (max {task['max_steps']})")
    if agent.report.get("stop_reason") not in ("goal_reached", None) and not task.get("expect_stop"):
        reasons.append(f"stopped early: {agent.report['stop_reason']}")
    if task.get("expect_stop") and agent.report.get("stop_reason") != task["expect_stop"]:
        reasons.append(f"expected stop '{task['expect_stop']}' but got '{agent.report.get('stop_reason')}'")
    return reasons


def run_eval(make_agent, tasks_path="golden_tasks.json", label="run", out="eval_report.json",
             runner=None, quiet=False):
    """
    make_agent: zero-arg function returning a FRESH agent with your tools registered.
    runner: optional fn(agent, goal)->answer to evaluate a wrapper (e.g. run_plan) instead of agent.run.
    """
    tasks = json.load(open(tasks_path))
    rows = []
    for t in tasks:
        agent = make_agent()
        t0 = time.time()
        answer = runner(agent, t["goal"]) if runner else agent.run(t["goal"])
        reasons = check_task(t, answer, agent)
        rows.append({"id": t["id"], "type": t.get("type", ""), "passed": not reasons,
                     "reasons": reasons, "steps": agent.report.get("steps"),
                     "tool_calls": agent.report.get("tool_calls"),
                     "stop": agent.report.get("stop_reason"),
                     "seconds": round(time.time() - t0, 2)})
    passed = sum(r["passed"] for r in rows)
    summary = {"label": label, "passed": passed, "total": len(rows),
               "pass_rate": round(passed / len(rows), 2) if rows else 0,
               "avg_steps": round(sum(r["steps"] or 0 for r in rows) / max(len(rows), 1), 1)}
    if not quiet:
        print(f"\n=== EVAL: {label} ===")
        print(f"{'id':<6}{'type':<12}{'result':<7}{'steps':>6}{'calls':>7}  stop / why")
        print("-" * 78)
        for r in rows:
            why = r["stop"] if r["passed"] else "; ".join(r["reasons"])
            print(f"{r['id']:<6}{r['type']:<12}{'PASS' if r['passed'] else 'FAIL':<7}"
                  f"{r['steps']:>6}{r['tool_calls']:>7}  {why}")
        print("-" * 78)
        print(f"pass rate {passed}/{len(rows)} = {summary['pass_rate']:.0%}   "
              f"avg steps {summary['avg_steps']}")
    json.dump({"summary": summary, "rows": rows}, open(out, "w"), indent=2)
    return summary
