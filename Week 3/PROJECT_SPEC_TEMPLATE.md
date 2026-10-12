# PROJECT_SPEC.md — copy this file into your project folder and fill it in

> If you cannot fill in every box, you do not have a project yet — you have an idea.
> The spec is what turns an idea into something you can build, test and demo.
> Worked example: `project_kit/example_support_desk/` (spec below mirrors it).

## 1. The pitch (one sentence — no more)
A **[type of] agent** that helps **[who]** do **[what]** so that **[benefit]**.

> Example: A support-desk agent that helps a customer-service rep look up orders,
> open tickets and request refunds, so that routine cases take one message instead of five tabs.

## 2. The user and the situation
- Who uses it? ______________________
- What do they type? (one real example message) ______________________
- What does a *good* result look like? ______________________

## 3. Tools (3–6) — each one is a Python function + a schema
| # | Tool name | Inputs | Returns | Changes something? | Risky? (needs approval) |
|---|-----------|--------|---------|--------------------|-------------------------|
| 1 | | | | no | no |
| 2 | | | | | |
| 3 | | | | | |

Rules: at least **one read tool**, at least **one tool whose output feeds another tool**
(that is what makes it an agent), and **mark anything that moves money, sends messages or
deletes data as risky**. Every tool starts as a **mock** (fake, deterministic data).

## 4. Five golden tasks — your test set (this is the heart of the spec)
Write the exact goal you will type and how you will check the result *without a model*.

| id | type | goal (exact text) | tools that must be called | answer must contain | max steps |
|----|------|-------------------|---------------------------|---------------------|-----------|
| G1 | easy (1 tool) | | | | 3 |
| G2 | chain (tool B needs tool A's output) | | | | 5 |
| G3 | branch (what it sees decides what it does next) | | | | 7 |
| G4 | safety (a risky action, or a request it must refuse / ask approval for) | | | | 4 |
| G5 | edge (bad input / missing record / empty result) | | | | 3 |

## 5. Architecture choices (fill in Mon / Wed — one line each, with a reason)
| Layer | Used? | Why / why not |
|-------|-------|---------------|
| ReAct loop | yes (always) | |
| Planner (Mon) | yes / no | which golden task needs it? |
| Reflection (Wed) | yes / no | what is your rubric? what does your code-verifier check? |
| Approval gate | yes / no | which tools? |

## 6. Stop and safety rules
- Step budget: ___ · Tool-call budget: ___ · Time budget: ___ s
- Which tools need a human yes? ______________________
- What must the agent refuse or never do? ______________________

## 7. Out of scope (what you will NOT build this module)
______________________  ← naming this protects you from scope creep.

## 8. Definition of done for Milestone M3 (Wed 14 Oct)
See `MILESTONE_M3.md`. Short version: the agent passes **4 of your 5 golden tasks**,
with a saved trace, a pass-rate table, and a 90-second demo.
