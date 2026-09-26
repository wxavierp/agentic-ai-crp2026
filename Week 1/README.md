# Week 1 — Foundations of Agentic AI

Module 1. Three sessions (Mon 2h · Wed 2h · Sat 4h lab). This week is about
**building the mental model** — it is deliberately light on coding. You'll run a
few short demos, design an agent on paper, and finish by building one small,
real **agent loop**.

## Learning objectives
By the end of the week you can:
- Explain what an AI **agent** is and how it differs from an assistant.
- Name the **four parts** of every agent: goal, tools, memory, actions.
- Describe three LLM limits (hallucination, no-action, reasoning drift) and how agents address them.
- Trace the **agent loop**: observe → reason → act → evaluate.
- Run a working agent loop and design a blueprint of your own.

## Files (work in `skeleton/`, check `trainer/` if stuck)

| File | What it is | Coding? |
|------|-----------|---------|
| `00_setup_check.py` | Verify your environment + first LLM call | run only |
| `01_assistant_vs_agent.py` | Assistant (words) vs agent (tool) | 2 small TODOs |
| `02_llm_reasoning_limits.py` | See hallucination & reasoning drift | 1 small TODO |
| `03_agent_anatomy.py` | **Design your agent blueprint** — *deliverable* | fill the blueprint |
| `04_agent_loop.py` | **Build the agent loop** — the week's coding exercise | 4 TODOs |
| `05_reflection_loop.py` | Add self-check (reflect → retry) to the loop | 2 TODOs |
| `06_multi_tool_agent.py` | Two tools + choose one; safe (no-`eval`) calculator | 3 TODOs |
| `07_advanced_agent.py` | *Advanced:* native function calling + challenges | optional |

## How to run
```bash
cd "Week 1"
python skeleton/00_setup_check.py
python skeleton/01_assistant_vs_agent.py
# ...and so on
```

## Deliverables (bring to next Monday)
1. **Agent blueprint** — your completed `03_agent_anatomy.py` (`my_agent`).
2. **Working agent loop** — your completed `04_agent_loop.py` solving `(23 * 7) + 19 = 180`.
3. All files pushed to your course **GitHub repo**.

See **STUDENT_ACTION_ITEMS.md** for the full checklist.
