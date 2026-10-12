# Milestone M3 — Your Reasoning Agent  (due end of Session 10 · Wed 14 Oct)

One folder in your GitHub repo: **your project's agent**, built on the Week-2/3 spine,
that reasons, plans when needed, checks itself, stays in control — and can *prove* it works.

## What to push  (`my_project/`)
```
my_project/
├─ PROJECT_SPEC.md        ← filled in (from PROJECT_SPEC_TEMPLATE.md)
├─ project.py             ← your tools (mocks OK) + make_agent()
├─ golden_tasks.json      ← your 5 golden tasks
├─ kit_agent.py  kit_planner.py  kit_reflect.py  kit_eval.py   ← copied from project_kit/
├─ utils/llm_client.py
├─ run_demo.py            ← runs one task end-to-end and prints the trace
├─ eval_report.json       ← produced by kit_eval.run_eval
├─ trace.json             ← produced by agent.save_trace()
└─ README.md              ← one screen (template below)
```

## Checklist — 10 points
| # | Requirement | Pts |
|---|-------------|-----|
| 1 | `PROJECT_SPEC.md` complete: pitch, user, 3–6 tools, 5 golden tasks | 1 |
| 2 | Tools return a value or `error: ...` — they never raise (test: blank/bad input) | 1 |
| 3 | At least one **risky** tool behind the approval gate; denial handled gracefully | 1 |
| 4 | ReAct trace saved to `trace.json` for a multi-step task | 1 |
| 5 | **Planner** used on at least one golden task (plan JSON visible), *or* a written reason it is not needed | 1 |
| 6 | **Reflection** with a rubric + a code verifier; budget ≤ 2; "unverified" status handled | 1 |
| 7 | Budgets set (steps, tool calls, seconds) and repeat guard active | 1 |
| 8 | `eval_report.json` shows **≥ 4 of 5** golden tasks passing | 1 |
| 9 | One **failure found and fixed**: README shows before/after for a failing task | 1 |
| 10 | 90-second live demo + README | 1 |

**Pass = 7 or more points, and it must include items 4 (trace), 8 (eval) and 10 (demo).**

## README.md template (keep it to one screen)
```
# <Project name>
<the one-sentence pitch>

## Run it
pip install -r requirements.txt   # + .env with LLM_PROVIDER=groq
python run_demo.py

## Tools
<table: name · what it does · risky?>

## Results (from eval_report.json)
pass rate: _/5   avg steps: _

## One failure I found and fixed
Task: ...   Before: ...   Fix: ...   After: ...

## What I'd add next (Module 4: memory)
...
```

## 90-second demo script
1. (10 s) The pitch sentence.  2. (30 s) Run one multi-step task; point at the trace.
3. (20 s) Show the approval gate stopping a risky action.  4. (20 s) Show the eval table.
5. (10 s) The one failure you fixed.
