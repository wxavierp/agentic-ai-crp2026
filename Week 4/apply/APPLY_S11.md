# Apply to your project - Session 11 (last 30 minutes)

Goal for tonight, small on purpose: **your agent remembers something across two runs, with the guards on.**

## Steps

1. **Copy** `Week 4/kit_memory.py` next to `kit_agent.py` in your project. (It uses only the standard library.)
2. **Short-term.** Keep a `ConversationMemory` in your chat loop and build the prompt with `with_memory(...)`:

```python
from kit_memory import ConversationMemory, FactStore, memory_tools, with_memory

store = FactStore("memory.json", user_id="u1")        # ONE user per FactStore
mem   = ConversationMemory(max_turns=10)              # or summarize=llm_summarizer(client), keep_last=5

for fn, schema in memory_tools(store):                # remember_fact / recall_fact / forget_fact become TOOLS
    agent.register(fn, schema)

def chat(user_text):
    agent.system = with_memory(BASE_SYSTEM, store, mem)
    answer = agent.run(user_text)
    mem.add_turn(user_text, answer)
    return answer
```

3. **Long-term.** Make the agent *use* the tools: add one line to your system prompt, e.g. *"When the user states a preference or constraint, save it with remember_fact. Before answering about the user, look it up with recall_fact."*
4. **Decide in writing** (one line each): what my agent **remembers**; what it **never stores**; when a fact **expires**.
5. **Test over two runs:** run the program, tell the agent something, quit, start again, ask. Then say "forget it" and ask again.
6. **Write in your `REASONING_LOG.md`**: what changed, one thing the test showed you, and one hazard (stale / incorrect / poisoned / sensitive) your agent could suffer.

## If it does not work

| Symptom | Likely cause |
|---|---|
| `ModuleNotFoundError: kit_memory` | the file is not next to `kit_agent.py` |
| the agent never calls `recall_fact` | the system prompt does not tell it to |
| it remembers for the wrong person | check `user_id` |
| a fact it should refuse got saved | look at `store.audit()` - that lists what the read-time guard refuses |

## Save (do not delete or edit)

* `Week 4/evidence/s11/` - results and check files from both activities.
* Your project changes (commit on your branch) and the REASONING_LOG paragraph.

## Coming up

Session 12 (Wed 28 Oct): **state** - checkpoint and resume, so your agent survives a crash in the middle of a job; and a test matrix for memory. Bring your project.
