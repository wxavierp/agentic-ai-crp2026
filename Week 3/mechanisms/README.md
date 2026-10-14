# mechanisms/ — the idea with nothing hiding it

Short scripts that run with **no API key and no network**. Each isolates ONE concept in ~20 lines of logic.
Output is **deterministic**: everybody gets the same result. The "models" and "critics" are small labelled
stand-ins; the real agents in `project_kit/` use a real model.

## How you use them (Session 10): explain -> watch -> try
Run everything through the companion from the `Week 3` folder:

| Step | Command | What happens |
|------|---------|--------------|
| setup | `python mechanisms/run_mechanism.py check` | asks for your roster number once; prints READY |
| WATCH | `python mechanisms/run_mechanism.py m1` (also `m2`, `m3`, `m4`) | runs the demo while the instructor explains it - no questions |
| TRY | `python mechanisms/run_mechanism.py m1 try` | 3 NEW situations. **You answer first** (cannot skip); your answers are saved with a time stamp; then the computer shows the truth and why |
| bug hunt | `python mechanisms/run_mechanism.py bug` | your file = roster number mod 5. Run once for phase 1 (no AI), again for phase 2 (AI allowed) |
| receipt | `python mechanisms/run_mechanism.py receipt` | prints ONE line to submit (Milestone M3, Part B) |

| Script | Concept | You will be asked (in `try`) |
|--------|---------|------------------------------|
| `m1_reflect_naked.py` | A checker can only judge what it can see; code first; budget and status | who flags a correct answer / right id with clipped wording; status with budget 1 |
| `m2_guards_naked.py` | Budgets and the repeat guard | where do three new configurations stop, and which guard |
| `m3_injection_naked.py` | Tool output is data, not orders | does the refund run under three new defences |
| `m4_eval_table.py` | Reading an eval table | calls/pass of a new variant, which task one layer fixed, a ship decision |
| `bughunt/bug_A..E.py` | Debugging from symptoms | each file has ONE planted bug |

`project_kit/kit_predict.py` applies the same habit to YOUR agent: `predict_then_run(agent, goal)` saves your
prediction (timestamped) before the run, then prints a scorecard.

Rule of the day: AI is allowed. When the terminal asks you a question, answer it yourself first.
