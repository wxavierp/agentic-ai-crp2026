"""
ablate.py - find which memory entries CHANGE what the agent does.

For each of the 6 tasks it runs the naive agent with the whole memory file (twice, to see if the answer is stable), then runs it
again with ONE entry removed at a time.  If removing an entry changes the action, that entry was steering the agent.
That is 6 x 2 + 17 x 6 = 114 short calls (a few cents with gpt-4o-mini).

    python ablate.py                 # real model from your .env
    python ablate.py --workers 2
    python ablate.py --offline       # REHEARSAL ONLY (the checker does not accept it)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", ".."))
import time
from common import get_roster, evidence_dir, save_json, load_json
import poison_lib as L


def main(argv):
    offline = "--offline" in argv
    workers, args, skip = 4, [], False
    for i, a in enumerate(argv):
        if skip: skip = False
        elif a == "--workers": workers, skip = int(argv[i + 1]), True
        elif not a.startswith("--"): args.append(a)
    roster = get_roster(args[0] if args else None)
    path = os.path.join(evidence_dir("s11"), "store.json")
    if not os.path.exists(path):
        sys.exit("run  python make_store.py  first")
    store = load_json(path)
    if store.get("hash") != L.make_store(roster)["hash"]:
        sys.exit("store.json is not the file for your roster number - run make_store.py again")
    if offline:
        act, model = L.OfflineAgent().act, L.OfflineAgent.name
        print("OFFLINE stand-in: a rehearsal only.\n")
    else:
        from naive_agent import make_act
        try:
            act, model = make_act()
        except Exception as e:
            sys.exit(f"Could not create the model client: {e}")
    print(f"roster {roster}   model {model}   (about 114 calls)")
    t0 = time.time()
    try:
        abl = L.run_ablation(store, act, workers=workers)
    except Exception as e:
        sys.exit(f"\nThe model call failed: {e}\nNothing was saved.")
    abl.update({"version": 1, "roster": roster, "store_hash": store["hash"], "model": model, "seconds": round(time.time() - t0, 1)})
    abl["seal"] = L.seal(store["hash"], abl, model)
    ev = evidence_dir("s11")
    save_json(os.path.join(ev, "ablation.json"), abl)
    print("\n" + L.format_influence(store, abl))
    tmpl = os.path.join(ev, "poison_findings.json")
    if not os.path.exists(tmpl):
        rows = [{"id": e["id"], "class": "TODO", "evidence": "", "changed_behavior": False} for e in store["entries"]]
        save_json(tmpl, {"roster": roster, "entries": rows, "rule": "TODO: ONE rule, 15+ words"})
        print(f"\nfindings template: {tmpl}")
    print("\nNow classify EVERY entry (ok / stale / incorrect / poisoned / sensitive) in poison_findings.json, then:  python check.py")
    if offline:
        print("(offline rehearsal - the checker will not give credit for this run)")


if __name__ == "__main__":
    main(sys.argv[1:])
