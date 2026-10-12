# Week 3 — Agent Architectures & Reasoning

Module 3. Three sessions (Sat 4h · Mon 2h · Wed 2h). This week the agent stops
just *looping* and starts *reasoning*. You'll build three architectures on top
of the Week 2 tool-calling engine — **ReAct**, **planning**, and **reflection**
— and make the whole thing **controllable** (it always stops cleanly). By
Session 10 you'll have the **reasoning agent**: the Module-3 milestone.

> Everything routes through the same `utils/llm_client.py` (`chat()` for native
> tool calling, `get_completion()` for plain prompts). No new required installs.

## Learning objectives
By the end of Week 3 you can:
- Explain and build a **ReAct** loop — Thought → Action → Observation → Answer — with a **reasoning trace**.
- **Plan** a task: decompose a goal into subtasks, execute them, and synthesise an answer.
- Add a **reflection** loop (critique → revise → confirm) with a reflection **budget**.
- Make an agent **controllable**: step budget, repeat guard, and other stop conditions.
- **Compare variants** on the same tasks — your first taste of evaluation (Module 7).

## Provider note
Use `LLM_PROVIDER=groq` (free) for every lab — these files use native tool
calling (`chat()`), spoken by **OpenAI, Groq and Ollama**. Planning and
reflection make several model calls per run, so the free Groq tier is ideal.

## Files (work in `skeleton/`, check `trainer/` if stuck)

| File | What it is | Coding? |
|------|-----------|---------|
| `00_arch_setup_check.py` | Confirm multi-step tool calling works | run only |
| `01_react_agent.py` | **ReAct agent** — reason/act loop + a trace | 3 TODOs |
| `02_planner_agent.py` | **Planner agent** — plan → execute → synthesise | 3 TODOs |
| `03_reflection_agent.py` | **Reflection** — critique → revise → confirm (budgeted) | 3 TODOs |
| `04_controllable_agent.py` | **Control & compare** — stop conditions + variant comparison | 3 TODOs |
| `05_langgraph_react.py` | *Optional* — the same ReAct loop as a LangGraph graph | 2 TODOs |

All demo tools are **deterministic and offline** (no API key, no network), so
labs run anywhere. `05` is optional and needs `pip install langgraph`.

## How to run
```bash
cd "Week 3"
python skeleton/00_arch_setup_check.py
python skeleton/01_react_agent.py
# ...and so on
```

## Your project (Days 9–10 → Milestone M3)
From Day 9 the labs are built on **your own project**. Start with these files:

| File | Use |
|------|-----|
| `PROJECT_MENU.md` | six ready-to-build project ideas (or bring your own) |
| `PROJECT_SPEC_TEMPLATE.md` | the one-page spec: pitch · tools · 5 golden tasks · architecture · safety |
| `project_kit/` | reusable `ProjectAgent`, planner, reflection, eval harness + a worked Support Desk example |
| `MILESTONE_M3.md` | the 10-point checklist, folder layout, README template, demo script |

## Deliverables (the Module-3 milestone — due Session 10 / Wed)
**Primary:** your project's reasoning agent — see `MILESTONE_M3.md`. The older demo-agent
deliverables below remain as the reference skeleton path.

1. **ReAct agent** — `01_react_agent.py` runs and prints a reasoning trace.
2. **Planner agent** — `02_planner_agent.py` prints a plan and a final answer.
3. **Reflection + control** — `03` reflects within a budget; `04` enforces a
   repeat guard and reports steps/tool-calls, with a variant comparison.
4. All files pushed to your course **GitHub repo**.

See **STUDENT_ACTION_ITEMS.md** for the full checklist.
Fast finishers: **EXTENSION_CHALLENGES_D1.md** (Day 8 extension challenges).
