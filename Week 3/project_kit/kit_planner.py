"""
kit_planner.py — add PLAN-THEN-EXECUTE to any agent (Day 9).

Works with any agent that has:  .client  .schemas  .functions  ._run_tool(call)
(ProjectAgent, or your Day-8 ReActAgent).  Your tools do not change.

    from kit_planner import run_plan
    out = run_plan(agent, "Customer a@x.com says order A100 is late - sort it out")
    print(out["answer"]);  print(out["plan"])

The pattern:  PLAN (as JSON data) -> CHECK -> [APPROVE] -> EXECUTE each step
              -> RE-PLAN if a step fails -> SYNTHESISE one answer.
"""

import json, re

MAX_PLAN_STEPS = 6
MAX_STEP_LOOPS = 5

PLAN_PROMPT = """You are the PLANNER for an agent. The agent can ONLY use these tools:
{tools}

Goal: {goal}
{extra}
Break the goal into {lo}-{hi} ordered steps. Each step must be small and checkable.
Reply with ONLY this JSON, no other text:
{{"steps": [{{"id": 1, "task": "what to do, in one sentence", "tool": "<one tool name above, or null>"}}]}}

Rules:
- "tool" must be exactly one of the names above, or null for a step that only reasons.
- A later step may use results of earlier steps.
- Do not invent tools. Do not add steps the goal does not need."""


# ---------------------------------------------------------------- PLAN
def tool_menu(agent):
    return "\n".join(f"- {s['function']['name']}: {s['function'].get('description', '')}"
                     for s in agent.schemas)


def parse_plan(text):
    """JSON first; if the model ignored the format, fall back to a numbered list."""
    text = text or ""
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            steps = json.loads(m.group(0)).get("steps", [])
            clean = [{"id": i, "task": str(s.get("task", "")).strip(), "tool": s.get("tool")}
                     for i, s in enumerate(steps, 1) if str(s.get("task", "")).strip()]
            if clean:
                return clean
        except (ValueError, AttributeError):
            pass
    steps = []
    for line in text.splitlines():
        mm = re.match(r"^\s*\d+[.)]\s*(.+)$", line)
        if mm:
            steps.append({"id": len(steps) + 1, "task": mm.group(1).strip(), "tool": None})
    return steps


def check_plan(plan, agent):
    """Return a list of problems (empty list = plan is OK). Cheap, deterministic."""
    problems = []
    if not plan:
        return ["plan is empty"]
    if len(plan) > MAX_PLAN_STEPS:
        problems.append(f"plan has {len(plan)} steps (max {MAX_PLAN_STEPS})")
    known = set(agent.functions)
    for s in plan:
        if s.get("tool") and s["tool"] not in known:
            problems.append(f"step {s['id']} uses unknown tool '{s['tool']}'")
    return problems


def make_plan(agent, goal, extra="", lo=2, hi=MAX_PLAN_STEPS, tries=2):
    """Ask for a plan; if check_plan finds problems, ask again once with the problems."""
    feedback = extra
    plan = []
    for _ in range(tries):
        prompt = PLAN_PROMPT.format(tools=tool_menu(agent), goal=goal, extra=feedback,
                                    lo=lo, hi=hi)
        plan = parse_plan(agent.client.get_completion(prompt, temperature=0.0, max_tokens=500))
        problems = check_plan(plan, agent)
        if not problems:
            return plan
        feedback = "\nYour previous plan was rejected: " + "; ".join(problems) + ". Fix it.\n"
    return plan            # best effort; the caller can still inspect/reject it


# ---------------------------------------------------------------- EXECUTE
def execute_step(agent, step, context):
    """Run ONE step with a small tool loop. Returns (result_text, ok)."""
    messages = [
        {"role": "system", "content":
         "You complete ONE step of a larger plan. Use tools if needed; use only facts "
         "from tools or the context. Answer concisely with the facts the next step needs."},
        {"role": "user", "content":
         f"Context from earlier steps:\n{context or '(none yet)'}\n\n"
         f"Your step: {step['task']}"
         + (f"\nSuggested tool: {step['tool']}" if step.get("tool") else "")},
    ]
    last_failed = False                       # did the MOST RECENT tool call fail?
    for _ in range(MAX_STEP_LOOPS):
        result = agent.client.chat(messages, tools=agent.schemas)
        if not result.wants_tools:
            text = (result.text or "").strip()
            return text, not (last_failed or text.lower().startswith("error"))
        messages.append(result.raw_message)
        for call in result.tool_calls:
            obs = agent._run_tool(call)
            last_failed = str(obs).startswith("error:")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(obs)})
    return "error: step hit its loop limit", False


# ---------------------------------------------------------------- SYNTHESISE
def synthesise(agent, goal, results):
    joined = "\n".join(f"- {t}: {r}" for t, r in results)
    prompt = (f"Goal: {goal}\n\nResults of each step:\n{joined}\n\n"
              "Write the final answer to the goal using ONLY these results. "
              "If a step failed, say so plainly instead of guessing.")
    return agent.client.get_completion(prompt, temperature=0.2, max_tokens=400)


# ---------------------------------------------------------------- DRIVER
def ask_plan_ok(plan):
    reply = input("\nRun this plan? [y/N] ")
    return reply.strip().lower() in ("y", "yes")


def run_plan(agent, goal, approve_plan=None, max_replans=1, verbose=True):
    """
    plan -> check -> (approve) -> execute -> (re-plan on failure) -> synthesise.
    approve_plan: fn(plan)->bool. Use ask_plan_ok for a human gate; None = auto-run.
    Returns {"answer","plan","results","replans","status"}.
    """
    plan = make_plan(agent, goal)
    if verbose:
        print("PLAN:")
        for s in plan:
            print(f"  {s['id']}. {s['task']}   [{s.get('tool') or 'reasoning'}]")
    if approve_plan and not approve_plan(plan):
        return {"answer": "Plan rejected by a human; nothing was executed.", "plan": plan,
                "results": [], "replans": 0, "status": "plan_rejected"}

    results, context, replans = [], "", 0
    queue = list(plan)
    while queue:
        step = queue.pop(0)
        text, ok = execute_step(agent, step, context)
        if verbose:
            print(f"  step {step['id']} {'OK ' if ok else 'FAIL'} -> {text}")
        results.append((step["task"], text))
        context += f"\n{step['task']}: {text}"
        if not ok and replans < max_replans:                       # RE-PLAN once
            replans += 1
            extra = (f"\nWork done so far:{context}\nThe last step FAILED: "
                     f"'{step['task']}'. Plan ONLY the remaining work, avoiding what failed.\n")
            queue = make_plan(agent, goal, extra=extra)
            if verbose:
                print(f"  RE-PLAN #{replans}: " + " | ".join(s['task'] for s in queue))
        elif not ok:
            break                                                  # out of re-plans: stop

    status = "ok" if not any(r[1].lower().startswith("error") for r in results) else "partial"
    return {"answer": synthesise(agent, goal, results), "plan": plan, "results": results,
            "replans": replans, "status": status}
