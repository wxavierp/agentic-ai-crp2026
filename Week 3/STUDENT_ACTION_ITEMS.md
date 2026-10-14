# Week 3 — Student Action Items

Tick these off as you go. Week 3 is where your agent starts to *reason*.

## Before Day 8 (Sat 10 Oct)
- [ ] Week 2 finished and pushed (`03_tool_calling_agent.py` = 65; `04_api_tool.py` robust)
- [ ] `LLM_PROVIDER` is **groq** (free), **openai**, or **ollama** (tool calling needs one)
- [ ] `python "Week 3/skeleton/00_arch_setup_check.py"` prints a FINAL answer (Dubai is hotter)
- [ ] Revise for the **End-of-Week-2 test** (taken at the start of Day 8)

## Day 8 — ReAct & reasoning traces (Sat 10 Oct)
- [ ] Sit the End-of-Week-2 test (solo, closed-notes)
- [ ] Watch the demo + code walkthrough (trainer/01) — you'll fill the same loop next

**Lab 1 — build the ReAct loop (`skeleton/01_react_agent.py`).** Everything else is
given; you write only the three parts inside `run()`:
- [ ] Run `00_arch_setup_check.py` — confirm multi-step tool calling works (Groq free)
- [ ] **TODO 1 · REASON** — `self.client.chat(messages, tools=self.schemas)`; the reply's text is the Thought
- [ ] **TODO 2 · STOP** — if `not result.wants_tools`: log the thought and `return result.text`
- [ ] **TODO 3 · ACT/OBSERVE** — append `result.raw_message`; run each tool; append the step to `self.trace`; append a `{"role":"tool", ...}` message
- [ ] Run it on "which is hotter now, Dubai or London?" — your trace should print like the demo
- [ ] Push your working `01_react_agent.py`

**Lab 2 — trace & compare.**
- [ ] Print the full trace; read it end to end
- [ ] Weaken the system prompt (drop "think step by step") and re-run the same goal
- [ ] Compare: what changed in the reasoning? how many steps each version took?
- [ ] *Stretch:* add a second tool and a goal that needs both
- [ ] *Optional:* try `05_langgraph_react.py` (`pip install langgraph`)
- [ ] Push your work

**Finished early? Work on YOUR project** — not the demo agent. Follow
**`EXTENSION_CHALLENGES_D1.md`** (the `PROJECT_GUIDE.md` path: scope → mock-first →
go real): list your project's tools, write one real ReAct trace by hand, then stand up
your own agent and get a mocked tool reasoning with a trace. Each step has a *"Done
when…"* check. This is real capstone progress, not a throwaway exercise. **Already mocked your tools?** Do the **Level 2** challenges (chain it, branch it, break-it-then-guard) — real reasoning on your own agent.

## Day 9 — Planning agents + your project spec (Mon 12 Oct)
From today the lab **is your project**. Start from `PROJECT_MENU.md` if you have no idea yet.
- [ ] **Spec (18 min):** copy `PROJECT_SPEC_TEMPLATE.md` → your project folder as `PROJECT_SPEC.md`; fill the pitch, 3–6 tools, and **5 golden tasks** (easy · chain · branch · safety · edge). *Done when* a neighbour can predict which tools each task calls.
- [ ] **Copy the kit (3 min):** `Week 3/project_kit/` → `kit_agent.py`, `kit_planner.py`, `utils/` into your project folder
- [ ] **Wire your tools (7 min):** `project.py` with `make_agent()` registering your mocked tools; `risky=True` on anything that writes/spends/sends
- [ ] Run **G1** with `agent.run(...)`; if the wrong tool is picked, fix the tool **description**
- [ ] Run a chain/branch golden task with `run_plan(agent, goal)`; read the printed plan aloud
- [ ] Break it on purpose (a mock returns `error: ...`) — does it re-plan or stop cleanly?
- [ ] Save the plan (`plan_G3.json`); write *Planner: yes/no because…* in `PROJECT_SPEC.md` §5
- [ ] Push (`day9: project spec + planner`)
- [ ] **Before Wednesday:** run all 5 golden tasks, save **one failing trace** (`agent.save_trace("fail_G3.json")`), push

> The skeleton lab `02_planner_agent.py` is now an optional reference (the concept in 60 lines). The kit's `kit_planner.py` is the version you use.

## Day 10 — Reflection, control & the milestone (Wed 14 Oct)
Tonight is **concept-first**. Each idea: the instructor **explains** it with a worked example, **runs** a demo you follow, then you **try** new situations in your own terminal (you answer first, then the computer reveals the truth). AI is allowed; the terminal asks for YOUR answer first.
- [ ] Before 8 PM: know your **roster number**; in `Week 3/` run `git pull`, then `python mechanisms/run_mechanism.py check` (prints READY)
- [ ] Act 1 Reflection: watch `m1`, then `python mechanisms/run_mechanism.py m1 try`
- [ ] Act 2 Control: watch `m2`, then `... m2 try`; then the **bug hunt**: `python mechanisms/run_mechanism.py bug` (phase 1: NO AI for ~4 minutes; run it again for phase 2 - AI allowed)
- [ ] Act 3 Injection: watch `m3`, then `... m3 try`
- [ ] Act 4 Evals: watch `m4`, then `... m4 try` (read the table; defend a ship decision)
- [ ] Short writing blocks (REASONING_LOG, not submitted tonight): 3 claims your agent makes; which tools your agent must NOT have; 3 new golden tasks
- [ ] End of session: `python mechanisms/run_mechanism.py receipt` and submit the ONE line (starts with `D10.`) in the Form

## Milestone M3 — your reasoning agent AND your understanding (due **Fri 16 Oct, 11:59 PM**)
Full 20-point rubric, folder layout and README template: **`MILESTONE_M3.md`**. **Part A** (it works) and **Part B** (you understand it) both must pass.
- [ ] **Part A:** `PROJECT_SPEC.md` · tools (never raise) · risky tool gated · `trace.json` · planner (or a written reason not) · reflection with rubric + verifier · budgets + repeat guard · `eval_report.json` ≥ 4/5 · one failure fixed (before/after) · README + 90-second demo
- [ ] **Part B:** Session-10 receipt submitted · ≥ 3 predictions on YOUR agent via `kit_predict` (misses explained in `REASONING_LOG.md`) · one bug explained from its trace · **walkthrough video** answering your 3 personal prompts (`python instructor_tools/walkthrough_prompts.py <your roster number>`) · honest AI-use log
- [ ] Pushed to your GitHub repo (a random third of the class gets a 5-minute live follow-up)

> `03_reflection_agent.py` and `04_controllable_agent.py` remain as optional reference skeletons.

## Next (Module 4 — memory)
- [ ] Add one sentence to `PROJECT_SPEC.md`: *"My agent should remember ___ between sessions, because ___."*

## Reflect (optional, 5 min)
- Where did a reasoning trace make a bug obvious that a bare answer would have hidden?
- Which stop condition would you add first to an agent you'd actually ship — and why?
