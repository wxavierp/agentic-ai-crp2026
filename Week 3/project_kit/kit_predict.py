"""
kit_predict.py - PREDICT, COMMIT, THEN RUN.

The cheapest way to stop "paste it into the AI and move on": before the agent runs, YOU
write down what it will do. Your prediction is saved with a timestamp BEFORE the run, so it
cannot be edited afterwards. Then the real run happens and you get a scorecard.

    from kit_predict import predict_then_run
    result = predict_then_run(agent, "Find asha's delayed order and open a ticket")

You are asked 3 things:
    1. how many steps will it take?             (a number)
    2. which tools, in order?                   (comma separated, e.g. find_customer,get_orders)
    3. why will it stop?                        (goal_reached / step_budget / tool_budget /
                                                  repeat_guard / time_budget)
Score: 1 point each (steps within +-1, tools in the same order, same stop reason).
Everything is appended to predictions.jsonl - paste the scorecard into REASONING_LOG.md.
"""
import json, time

STOP_REASONS = ["goal_reached", "step_budget", "tool_budget", "repeat_guard", "time_budget"]


def _tools(text):
    return [t.strip() for t in text.split(",") if t.strip()]


def ask_prediction(ask=input):
    def read(q):
        try:
            return ask(q).strip()
        except EOFError:
            return ""
    print("\nPREDICT before it runs (write yours FIRST - then you may compare with an AI's guess).")
    steps = read("  1) How many steps will the agent take? (a number): ")
    tools = read("  2) Which tools, in order? (comma separated, or empty for none): ")
    stop = read(f"  3) Why will it stop? ({' / '.join(STOP_REASONS)}): ")
    return {"steps": int(steps) if steps.isdigit() else None, "tools": _tools(tools), "stop_reason": stop}


def score(pred, report, trace):
    actual_tools = [s["action"] for s in trace if s["action"]]
    checks = {
        "steps (+-1)": pred["steps"] is not None and abs(pred["steps"] - report["steps"]) <= 1,
        "tools, in order": pred["tools"] == actual_tools,
        "stop reason": pred["stop_reason"] == report["stop_reason"],
    }
    return checks, actual_tools


def predict_then_run(agent, goal, ask=input, logfile="predictions.jsonl", runner=None):
    pred = ask_prediction(ask)
    with open(logfile, "a") as f:                                   # committed BEFORE the run
        f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "prediction",
                            "goal": goal, **pred}) + "\n")
    print("\nPrediction saved (timestamped). Running...\n")
    answer = (runner or agent.run)(goal)
    checks, actual_tools = score(pred, agent.report, agent.trace)
    with open(logfile, "a") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "actual", "goal": goal,
                            "steps": agent.report["steps"], "tools": actual_tools,
                            "stop_reason": agent.report["stop_reason"],
                            "points": sum(checks.values())}) + "\n")
    print("\n=== PREDICTION vs REALITY ===")
    print(f"  you said : steps={pred['steps']}  tools={pred['tools']}  stop={pred['stop_reason'] or '-'}")
    print(f"  reality  : steps={agent.report['steps']}  tools={actual_tools}  stop={agent.report['stop_reason']}")
    for k, ok in checks.items():
        print(f"  {'OK ' if ok else 'MISS'} {k}")
    print(f"  SCORE {sum(checks.values())}/3   <- a MISS is where your mental model is wrong. "
          "Write one sentence in REASONING_LOG.md about why.")
    return {"answer": answer, "prediction": pred, "checks": checks,
            "points": sum(checks.values()), "report": agent.report}
