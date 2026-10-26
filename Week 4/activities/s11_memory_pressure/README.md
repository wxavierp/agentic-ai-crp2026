# Activity 1 - Memory under pressure (30 minutes)

A standalone script exercise. It is **not** part of your project: you will measure how much of a conversation a model can still use under different memory strategies, on a conversation that belongs to **your roster number only**.

## What you do

| Min | Step | Command |
|---|---|---|
| 0-3 | Build your case and look at where the 8 hidden facts are | `python make_case.py` (add `--show` to read the whole conversation) |
| 3-8 | Run all 9 strategies against a real model (a few cents with `gpt-4o-mini`, free with a local model) | `python run_eval.py` |
| 8-22 | **Your analysis** (this is the real task) - edit `evidence/s11/pressure_analysis.json` | see below |
| 22-30 | Check it, fix what the checker says, save | `python check.py` |

`run_eval.py` first prints a table: 8 facts (F1-F8) x 9 strategies (`window-5` ... `window-40` = "the model sees only the last N turns"; `summary300+5` = "one summary of everything older than the last 5 turns, plus the last 5 turns"). Rubric per cell: `E` exact, `p` paraphrased, `~` partial, `.` absent, `*` an OLD value was given.

Run it with the model you will use in your project if you can. A different model gives different numbers - that is fine, the checker re-grades **your** run.

## The analysis you must write (`pressure_analysis.json`)

```json
{
  "roster": 17,
  "smallest_window_turns": 25,
  "lost_facts": [
    {"fact": "F3", "strategy": "window-15", "why_code": "outside_window",
     "why": "F3 was said at turn 25 but window-15 only sees turns 26-40, so the model never saw it"}
  ],
  "recommendation": "20+ words: which strategy for a customer-support agent, and why, using your own numbers"
}
```

* `smallest_window_turns` - the smallest `window-N` that scores 90% or more in **your** table, or `"none"`.
* `lost_facts` - at least 3 (fact, strategy) pairs that were **not** recalled, covering at least 2 different strategies and 2 different kinds of fact. For each one choose the real cause:
  * `outside_window` - the fact was older than the window. Your reason must name the turn it was said at.
  * `dropped_by_summary` - the fact was older than the last 5 turns and your summary left it out (read `summary_text` in `pressure_results.json`). Name the turn.
  * `stale_value` - the model gave an OLD value (look for `*` in the table).
  * `model_error` - the model could see the fact and still got it wrong.
* The checker compares each claim with your actual run, so a reason that does not fit your numbers is rejected.

## Rules

* One run per attempt is plenty. If you change the model, run again and redo the analysis - the checker refuses a results file that was edited after the run.
* The checker cannot know who typed the analysis. In class you may be asked to explain **one of your own numbers**: why a given fact was lost under a given strategy. If you understand your table, that takes 20 seconds.
* AI assistants are allowed for explaining things. They cannot do this task for you: the conversation, the answers and the table exist only on your machine.
* This is a memory-measurement exercise. Nothing here is a user's real data and nothing is shared between users.

## Offline rehearsal

`python run_eval.py --offline` uses a stand-in "model" that simply reads what it is shown. It lets you see the shape of the table with no key, but **the checker will not accept it**.

## If the checker says...

| Message | Meaning |
|---|---|
| `the results came from the OFFLINE stand-in` | Run `run_eval.py` without `--offline`. |
| `even the FULL history scored only N%` | Your model is too weak for this task. Try `gpt-4o-mini` or a larger local model and run again. |
| `... was INSIDE window-N, so it cannot be 'outside_window'` | Look at the turn number of that fact (`make_case.py` prints it): the window did see it. Pick the right cause. |
| `your summary DID keep ...` | Read `summary_text`: the summary contains that value, so "dropped_by_summary" is wrong. |
| `edited after the run` | Do not edit `pressure_results.json`; run again. |
