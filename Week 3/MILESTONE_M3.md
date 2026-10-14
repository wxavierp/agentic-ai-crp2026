# Milestone M3 - Your Reasoning Agent  (due **Fri 16 Oct, 11:59 PM Dubai time**)

Two parts, both required:

- **Part A - it works:** your project's agent reasons, plans when needed, checks itself, stays
  in control - and you can *prove* it works.
- **Part B - you understand it:** you can explain why it works, predict what it does, and debug it.
  A working agent that you cannot explain does not pass.

Using AI is allowed throughout. Part B is how you show that **you** are the one in charge of it.

## Part A - it works (10 points)  ·  folder layout
```
my_project/
├─ PROJECT_SPEC.md        ← filled in (from PROJECT_SPEC_TEMPLATE.md)
├─ project.py             ← your tools (mocks OK) + make_agent()
├─ golden_tasks.json      ← your golden tasks (the 5 + the 3 you wrote in Session 10)
├─ kit_agent.py  kit_planner.py  kit_reflect.py  kit_eval.py  kit_predict.py   ← from project_kit/
├─ utils/llm_client.py
├─ run_demo.py            ← runs one task end-to-end and prints the trace
├─ eval_report.json       ← produced by kit_eval.run_eval
├─ trace.json             ← produced by agent.save_trace()
├─ predictions.jsonl      ← produced by run_mechanism.py and kit_predict (timestamped predictions)
├─ REASONING_LOG.md       ← Part B (template: Week 3/REASONING_LOG.md)
├─ walkthrough.mp4 (or link) ← Part B
└─ README.md              ← one screen (template below)
```

| # | Requirement | Pts |
|---|-------------|-----|
| 1 | `PROJECT_SPEC.md` complete: pitch, user, 3-6 tools, 5 golden tasks | 1 |
| 2 | Tools return a value or `error: ...` - they never raise (test: blank/bad input) | 1 |
| 3 | At least one **risky** tool behind the approval gate; denial handled gracefully | 1 |
| 4 | ReAct trace saved to `trace.json` for a multi-step task | 1 |
| 5 | **Planner** used on at least one golden task (plan JSON visible), *or* a written reason it is not needed | 1 |
| 6 | **Reflection** with a rubric + a code verifier; budget ≤ 2; `unverified` / `needs_input` handled | 1 |
| 7 | Budgets set (steps, tool calls, seconds) and repeat guard active | 1 |
| 8 | `eval_report.json` shows **≥ 4 of 5** original golden tasks passing, plus your 3 new ones (one expected to fail, reported honestly) | 1 |
| 9 | One **failure found and fixed**: README shows before/after for a failing task | 1 |
| 10 | README + 90-second demo (video or live) that runs from a fresh clone | 1 |

**Part A pass = 7 or more points, and it must include items 4 (trace), 8 (eval) and 10 (demo).**

## Part B - you understand it (10 points)

| # | Evidence | Pts | What a full-marks answer looks like |
|---|----------|-----|-------------------------------------|
| B1 | **Session-10 receipt** (submitted via the Form) + **≥ 3 predictions on YOUR agent** (`kit_predict.predict_then_run`, logged in `predictions.jsonl`) with a one-sentence reason for each miss in `REASONING_LOG.md` section 1 | 3 | Receipt submitted; your own-agent predictions are timestamped before the runs; misses explained |
| B2 | One bug explained from its trace (log section 2) | 2 | Names the line, explains how it produces the symptom, shows before/after |
| B3 | **Walkthrough video** (3-4 min, screen showing your code) answering your 3 personal "what if" prompts | 4 | You change the code live, run it, and explain the difference - not just narrate what the code does |
| B4 | AI-use log (log section 4) | 1 | Specific entries; says what you checked; honest |

**Part B pass = 6 or more points.** Final M3 grade: Part A and Part B each count 50%.

### Your personal prompts for the walkthrough
```
python instructor_tools/walkthrough_prompts.py <your roster number>
```
You get 3 "change this, then explain what happens" prompts that depend on your roster number
(for example "set max_steps to 2 - which golden task fails and why?"). Do each live on your own
code: make the change, run it, show the result, explain it. A classmate's video, or a script an
AI wrote without you, cannot answer your prompts.

### Spot-check
About a third of the class (chosen at random) gets a 5-minute live follow-up on a video call.
If your code and your explanation do not match, you resubmit Part B. This is how we keep
Part B meaningful - it is not a penalty for using AI.

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
pass rate: _/8   avg steps: _   task I expected to fail: _  (result: _)

## One failure I found and fixed
Task: ...   Before: ...   Fix: ...   After: ...

## What I'd add next (Module 4: memory)
...
```

## 90-second demo script
1. (10 s) The pitch sentence.  2. (30 s) Run one multi-step task; point at the trace.
3. (20 s) Show the approval gate stopping a risky action.  4. (20 s) Show the eval table.
5. (10 s) The one failure you fixed.
