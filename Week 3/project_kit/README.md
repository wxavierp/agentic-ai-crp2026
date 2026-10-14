# project_kit — the reusable spine for your capstone

Copy these files into **your** project folder (keep `utils/llm_client.py` beside them).

| File | Day | What it gives you |
|------|-----|-------------------|
| `kit_agent.py` | 8 → 10 | `ProjectAgent`: ReAct loop + trace + budgets + repeat guard + approval gate + run report |
| `kit_planner.py` | 9 | `run_plan(agent, goal)`: JSON plan → check → (approve) → execute → re-plan → synthesise |
| `kit_reflect.py` | 10 | `reflect(agent, goal, rubric, verifier)`: code checks + rubric critic that sees the evidence |
| `kit_eval.py` | 10 | `run_eval(make_agent)`: golden tasks → pass-rate table + `eval_report.json` |
| `kit_predict.py` | 10 | `predict_then_run(agent, goal)`: you predict steps/tools/stop reason BEFORE the run (timestamped), then a scorecard |
| `example_support_desk/walkthrough_reflect.py` | 10 | ONE reflection round on the real agent with every hand-off printed (trace, `evidence()`, verifier, the critic prompt). `--offline` = scripted model, no key |
| `example_support_desk/` | all | a complete worked project: tools, golden tasks, demos |
| `tests/test_kit.py` | — | offline tests (no keys): `python tests/test_kit.py` |

Your tools never change: **register them once, wrap the agent in whichever layers you need.**

```python
from kit_agent import ProjectAgent, ask_human
from kit_planner import run_plan
from kit_reflect import reflect
agent = ProjectAgent(approve=ask_human)
agent.register(my_tool, MY_SCHEMA)
agent.register(send_email, SEND_SCHEMA, risky=True)
agent.run(goal)                                      # ReAct
run_plan(agent, goal)                                # planning
reflect(agent, goal, rubric=[...], verifier=check)   # reflection
```

## Demos ask for your goal (and keep talking)
`example_support_desk/demo_day2.py` and `demo_day3.py` show 2 suggested goals, then wait for input:
type **1** or **2**, write your **own** goal, or press **Enter** for suggestion 1. The helper is
`utils/cli.py` -> `ask_goal([...])`; reuse it in your own `run_demo.py`.
(No keyboard / piped input? It silently uses suggestion 1.)

**Chat loop:** after each answer the demo asks *"Reply / follow-up / new goal (press Enter to finish)"*.
If the agent asks you a question (e.g. "which email?"), just answer it - it sees the conversation so far.
`reflect()` now returns status `needs_input` when the agent asks a question instead of answering
(nothing to review yet), alongside `confirmed` and `unverified`.
