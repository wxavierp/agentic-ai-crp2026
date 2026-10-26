"""
naive_agent.py - the agent you are investigating.  READ IT, it is short.

It does the simplest thing that "works": it pastes EVERYTHING in the memory file into the prompt and lets the model decide.
No filtering, no checking of source, date or owner - exactly what happens when memory is added carelessly.

    python naive_agent.py T3         # run one task once and see what it does   (T1..T6, see poison_lib.TASKS)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", ".."))
from common import get_roster, evidence_dir, load_json
import poison_lib as L


def make_act():
    from utils.llm_client import LLMClient
    client = LLMClient()
    return (lambda messages: client.chat(messages, temperature=0.0, max_tokens=120).text or ""), f"{client.provider}/{client._default_model()}"


def main(argv):
    task = argv[0].upper() if argv else "T1"
    if task not in L.TASKS:
        sys.exit("task must be one of " + ", ".join(L.TASKS))
    get_roster()
    path = os.path.join(evidence_dir("s11"), "store.json")
    if not os.path.exists(path):
        sys.exit("run  python make_store.py  first")
    store = load_json(path)
    act, model = make_act()
    msgs = L.build_messages(store["entries"], task)
    print(f"[{model}]  task {task}: {L.TASKS[task]}\n")
    print(msgs[0]["content"].split("MEMORY FILE:")[1].strip(), "\n")
    out = act(msgs)
    print("model said :", out.strip())
    print("action     :", L.short(L.parse_action(out)))


if __name__ == "__main__":
    main(sys.argv[1:])
