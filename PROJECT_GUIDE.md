# From Exercises to Your Capstone

The weekly exercises aren't throwaway demos — they're the **scaffolding you copy
into your own project**. This guide shows how to turn what you built in the labs
into your capstone agent. The short version:

> **Copy `ToolAgent`, replace the demo tools with mocks of your project's
> actions, get the agent reasoning, then swap each mock for the real API —
> keeping the error contract. Your capstone is _your tools_ plus the reasoning
> layers from Week 3 on.**

---

## 1. The reusable spine never changes

Two things are domain-agnostic. Copy them into your project and don't rewrite them:

- **`utils/llm_client.py`** — the provider wrapper (`get_completion` + `chat`).
- **The `ToolAgent` class** — from `Week 2/.../03_tool_calling_agent.py` (and `05`/`07`).
  Register tools, then `.run(goal)` loops until the model answers, guarded by `MAX_STEPS`.

Everything else you build is just **adding tools**.

## 2. Adding a capability = one function + one schema + one `register()`

This is the pattern you practised all of Module 2. To give your agent a new power:

```python
def create_ticket(title: str, priority: str = "normal"):
    ...                       # your Python function (the "hands")
    return "..."              # a value, or an "error: ..." string

CREATE_TICKET_SCHEMA = {
    "type": "function",
    "function": {
        "name": "create_ticket",
        "description": "Open a support ticket. Use when the user reports a problem.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]},
            },
            "required": ["title"],
        },
    },
}

agent.register(create_ticket, CREATE_TICKET_SCHEMA)
```

Want your agent to look up a record, check inventory, send a message, or query a
database? Same three steps each time.

## 3. Build against a mock first (the key habit)

Don't wait for real API keys to start. Build the tool with a **deterministic
stub**, get the whole agent working, then swap in the real call:

**Step A — mock.** Return fake-but-realistic data (like the fake weather dict in
`01`, or `_mock_webhook` in `06`):

```python
def get_stock(sku: str):
    FAKE = {"A100": 42, "B200": 0}          # mock data — no network, no key
    n = FAKE.get(sku)
    return n if n is not None else f"error: unknown sku '{sku}'"
```

Register it and run the agent. Now the **reasoning** works — no keys, no network,
no cost, and repeatable output you can debug.

**Step B — go real.** Replace only the *inside* of the function with the real API
call. Keep the **same signature** and the **same error contract**. The agent code
does not change:

```python
def get_stock(sku: str):
    if not isinstance(sku, str) or not sku.strip():
        return "error: 'sku' must be a non-empty string"     # INPUT validation
    try:
        r = requests.get(API, params={"sku": sku}, timeout=8)
        r.raise_for_status()
        data = r.json()
        if "quantity" not in data:                            # OUTPUT validation
            return "error: response missing quantity"
        return data["quantity"]
    except requests.exceptions.Timeout:
        return "error: inventory API timed out"
    except requests.exceptions.RequestException as e:
        return f"error: network/API problem: {e}"
```

`06`'s `WEBHOOK_URL`-or-mock toggle is exactly this pattern ("mock in dev, real
in prod") — reuse it for any external action.

## 4. The error contract (never break it)

Every tool **returns** a value or an `"error: ..."` string. A tool **never
raises**. This is what lets the agent read a failure and recover instead of
crashing. It's the whole point of `04`, and it's non-negotiable in your capstone.

## 5. Grow your failure suite

`failure_suite()` in `07_milestone_agent.py` is your test template. For every new
tool, add the checks that prove it fails cleanly — blank input, bad input, and an
outage — so your agent stays crash-proof as it grows. Run it offline, every time.

## 6. Layer the reasoning (Week 3 and beyond)

Once you have a working `ToolAgent` for *your* domain, the later modules wrap it —
you don't touch your tools:

| Layer | From | What it adds |
|-------|------|--------------|
| **ReAct** | `Week 3/01_react_agent.py` | a visible Thought → Action → Observation trace |
| **Planning** | `Week 3/02_planner_agent.py` | decompose a goal into subtasks, then execute |
| **Reflection** | `Week 3/03_reflection_agent.py` | the agent critiques and improves its own answer |
| **Control** | `Week 3/04_controllable_agent.py` | stop conditions + comparing variants |
| **Memory / RAG / Multi-agent** | M4–M6 | state across sessions, your own knowledge, teams of agents |

Your tools stay the same; you drop the agent *inside* these wrappers.

## 7. Your starting checklist

1. **Fork the repo structure.** Keep `utils/llm_client.py`; copy the `ToolAgent` class.
2. **List your project's actions** — these are your tools (3–6 is plenty to start).
3. **Write each as a mock** (stub function + schema), register it, and run the agent
   until the reasoning is right.
4. **Swap each mock for the real API** — same signature, same error contract — and
   add it to your `failure_suite()`.
5. **Wrap it** in ReAct / planning / reflection as the project grows.
6. **Commit often.** One repo, growing into your capstone.

---

**Remember:** the labs already taught you every piece of this. The capstone is not
a new skill — it's the same `ToolAgent`, your own tools, and the reasoning layers
stacked on top. Start with mocks today; you don't need a single API key to begin.
