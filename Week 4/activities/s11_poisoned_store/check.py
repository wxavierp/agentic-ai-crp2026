"""
check.py - checks your Activity 2 evidence against YOUR memory file and YOUR ablation run.

    python check.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", ".."))
from common import get_roster, evidence_dir, save_json, load_json
import poison_lib as L


def check(ev_dir, roster):
    sp, ap, fp = (os.path.join(ev_dir, n) for n in ("store.json", "ablation.json", "poison_findings.json"))
    if not (os.path.exists(sp) and os.path.exists(ap)):
        return False, ["FAIL  run make_store.py and ablate.py first"], {}
    store, abl = load_json(sp), load_json(ap)
    bad = []
    want = L.make_store(roster)
    if store.get("hash") != want["hash"] or abl.get("store_hash") != want["hash"]:
        bad.append("these files do not belong to your roster number: run make_store.py and ablate.py again")
    if abl.get("model") == L.OfflineAgent.name:
        bad.append("the ablation came from the OFFLINE stand-in: run  python ablate.py  without --offline")
    if abl.get("seal") != L.seal(abl.get("store_hash"), abl, abl.get("model")):
        bad.append("ablation.json was edited after the run: run ablate.py again")
    if bad:
        return False, ["FAIL  " + b for b in bad], {}
    unstable = [t for t, ok in abl["stable"].items() if not ok]
    if len(unstable) > 2:
        return False, [f"FAIL  the model gave different answers to the SAME question in {len(unstable)} of 6 tasks, so the ablation says nothing. "
                       "Use a steadier model (gpt-4o-mini, temperature 0) and run ablate.py again"], {}
    if not os.path.exists(fp):
        return False, ["FAIL  no findings yet: edit evidence/s11/poison_findings.json"], {}
    findings = load_json(fp)
    if "TODO" in str(findings):
        return False, ["FAIL  poison_findings.json still has TODO in it"], {}
    store["_roles"] = {}
    problems = L.validate_findings(store, abl, findings)
    truth = L.truth(store)
    out = [f"{sum(1 for v in truth.values() if v != 'ok')} entries break a rule; {sum(1 for v in abl['changed'].values() if v)} of the 17 steered your agent in this run."]
    summary = {"roster": roster, "store_hash": store["hash"], "model": abl["model"],
               "steering_entries": sorted(k for k, v in abl["changed"].items() if v), "passed": not problems}
    if problems:
        return False, out + ["FAIL  " + p for p in problems], summary
    return True, out + ["PASS  every entry is classified by the rules, and your 'changed behaviour' claims match your own ablation."], summary


def main(argv):
    roster = get_roster(argv[0] if argv else None)
    ev = evidence_dir("s11")
    ok, lines, summary = check(ev, roster)
    print("\n".join(lines))
    if summary:
        save_json(os.path.join(ev, "poison_check.json"), summary)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
