# REASONING_LOG.md - your thinking, in your words

Copy this file into your project folder. It is **Part B of Milestone M3** - the graders read it
to see how you think. Short, specific and honest beats long and polished. Using AI is fine;
hiding it is not.

## 1. Predictions on YOUR agent (Milestone B1)
Tonight's predictions are recorded automatically by `mechanisms/run_mechanism.py` (your **receipt** is submitted via the Form).
Here, log at least **3 predictions about YOUR OWN agent**: use `kit_predict.predict_then_run(agent, goal)` - it saves your
prediction with a time stamp BEFORE the run and prints a scorecard. Paste the scorecard line and explain each miss.

| # | Goal I tried | What I predicted (steps / tools / stop) | What happened | If I missed: why was I wrong? (1 sentence) |
|---|--------------|------------------------------------------|---------------|---------------------------------------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## 2. One bug, explained from the trace (pick a bug in YOUR agent or the bug hunt)
- Symptom (what I saw):
- Where in the trace / eval row I saw it:
- The line responsible and why it causes the symptom:
- My fix, and the evidence it worked (before/after):

## 3. Three things I can explain without notes
(Examples: why the critic needs the evidence; why the repeat guard keys on tool + args; why the approval gate beats a prompt rule.)
1.
2.
3.

## 4. AI-use log
List every substantial use of an AI assistant for this milestone. Be specific.

| What I asked | What the AI said / produced (1 line) | What I checked myself (how) | What I changed or rejected |
|--------------|--------------------------------------|------------------------------|-----------------------------|
| | | | |

Rules: "I did not check it" is an acceptable entry - it is honest, and tells you what to check next.
An empty log when your code clearly used AI is not.

## 5. Exit ticket from Session 10 (3 lines)
- The check that would have caught my last bug is:
- One thing my AI assistant told me that I verified myself:
- One thing I would NOT trust my agent to do without approval:
