# Apply to your project - Session 12 (last 30 minutes)

Goal: bring the two ideas from tonight's labs into **your own agent**, and prove each one with a simple test you run by hand.

| Lab | The idea | What it becomes in your agent |
|---|---|---|
| Lab 1 - the job that paid twice | write down what is **done**; skip it after a restart | a **journal** of tool calls that already ran |
| Lab 2 - the chatbot that forgets | save facts to a **file**; replace on update; **really** forget | a fact store, and forgetting that also clears the conversation |

> These are **patterns to adapt**, not code to paste. Your agent's loop is not the same as the lab's, so you will need to adjust the surrounding code. A working reference is in the repo: `project/` (the Support Desk agent with both applied).

## Recipe 1 - make your agent restart-safe (about 12 minutes)
The four moves are the same as `job.py`:
1. **Decide** which of your tools must run only once per job - the ones that create, send, pay or delete something. Reading tools do not need it.
2. **Before** running such a tool: look in the journal. If this exact call (tool name + arguments) is there, return the saved result and **do not run it**.
3. **Run** the tool.
4. **Right after** it succeeded: write the call and its result into the journal (a file). Never write down a failed call.

When the whole goal is finished, clear the journal - the next run is a new job.

In the reference: `project/kit_state.py` (the journal, about 40 lines) and three small changes in `project/kit_agent.py` (`register(..., once=True)`, `add_journal()`, and a check inside `_run_tool`). Compare them with what you wrote in `job.py`.

## Recipe 2 - give your agent a memory that can forget (about 12 minutes)
1. **Facts file:** load, save (a new value for a slot *replaces* the old one), forget - as in `chat.py`. The reference is `Week 4/kit_memory.py` (`FactStore`, `memory_tools`).
2. **Forgetting must also clear the conversation.** If your agent keeps recent turns in its prompt, deleting the fact is not enough - remove the turns that mention it. In the reference: `ConversationMemory.scrub()` and `memory_tools(store, conversation)`.
3. Tell the agent in the system prompt **when** to save, recall and forget (see `project/example_support_desk/demo_memory.py`).

## Verify (about 6 minutes) - run each by hand and tick it
| Test | Expected |
|---|---|
| Start a job with 2+ actions; press **Ctrl-C** after the first; run it again | the completed action is **not** repeated |
| Let a job finish; run the **same** job again | a new job starts - it does the work again, on purpose (the journal was cleared) |
| Tell the agent a fact; quit; start again; ask | it still knows it |
| Tell it a fact, then **change** it; ask | it uses the latest value |
| Say "forget it"; ask (same session); quit, start, ask | it does not know it - both times |

If a test fails, find the line that is responsible before changing anything.

## Save (do not delete or edit)
* `job.py` and `chat.py` from the labs, as you finished them
* your project changes (commit on your branch)
* three lines in `REASONING_LOG.md`: what you added, which test you ran, what surprised you

## Coming up
Session 13 (Sat 31 Oct, 4 hours): retrieval - embedding models first, then chunking and search. Also: you will learn to build Gradio apps like the ones I used in demos.
