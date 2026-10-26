"""
check.py - checks your Activity 1 evidence.  It re-builds YOUR case from your roster number, re-grades your saved answers,
and compares what you wrote in the analysis with what your own run shows.

    python check.py            # uses evidence/s11/pressure_results.json and pressure_analysis.json

PASS means: a real model was used, nothing was edited after the run, and your analysis agrees with your numbers.
(It cannot know who typed the analysis. That is on you - and in class you may be asked to explain your numbers.)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", ".."))
from common import get_roster, evidence_dir, save_json, load_json
import pressure_lib as L


def check(ev_dir, roster=None):
    """-> (ok, lines, summary)  - pure function so it can be tested."""
    out, bad = [], []
    rp, ap = os.path.join(ev_dir, "pressure_results.json"), os.path.join(ev_dir, "pressure_analysis.json")
    if not os.path.exists(rp):
        return False, ["FAIL  no results yet: run  python run_eval.py"], {}
    results = load_json(rp)
    roster = results.get("roster") if roster is None else roster
    case = L.make_case(roster)
    if results.get("roster") != roster:
        bad.append(f"the results are for roster {results.get('roster')}, not {roster}")
    if results.get("case_hash") != case["hash"]:
        bad.append("the results do not belong to your case (wrong roster number, or the case generator changed): run make_case.py and run_eval.py again")
    if results.get("model") == L.OfflineModel.name:
        bad.append("these results came from the OFFLINE stand-in, not a real model: run  python run_eval.py  (without --offline)")
    if results.get("seal") != L.seal(results.get("case_hash"), results):
        bad.append("the results file was edited after the run (the seal does not match): re-run run_eval.py instead of editing it")
    strategies = results.get("strategies", {})
    for name in L.strategy_names():
        if name not in strategies:
            bad.append(f"strategy {name} is missing"); continue
        for f in case["facts"]:
            if not str(strategies[name].get("answers", {}).get(f["id"], "")).strip():
                bad.append(f"{name}: no answer for {f['id']}")
    if L.SUMMARY in strategies and not str(strategies[L.SUMMARY].get("summary_text", "")).strip():
        bad.append("the summary text is empty")
    if bad:
        return False, ["FAIL  " + b for b in bad], {}
    grades = L.compute_grades(case, results)
    out.append(L.format_table(case, grades))
    full = grades["window-40"]["score"]
    if full < 0.75:
        bad.append(f"even the FULL history (window-40) scored only {full * 100:.0f}%: this model cannot answer these questions reliably - "
                   "switch to a stronger model (see the README) and run again")
    want = L.smallest_window(grades)
    out.append(f"\nsmallest window that keeps >= {int(L.THRESHOLD * 100)}%: {want if want else 'none'}"
               f"   |   summary300+5 scored {grades[L.SUMMARY]['score'] * 100:.0f}%")
    if not os.path.exists(ap):
        bad.append("no analysis yet: edit evidence/s11/pressure_analysis.json (run_eval.py created a template)")
    else:
        analysis = load_json(ap)
        if "FILL IN" in str(analysis):
            bad.append("the analysis still contains FILL IN placeholders")
        else:
            bad += L.validate_analysis(case, results, grades, analysis)
    summary = {"roster": roster, "case_hash": case["hash"], "model": results.get("model"),
               "scores": {k: v["score"] for k, v in grades.items()}, "smallest_window_turns": want, "passed": not bad}
    if bad:
        return False, out + ["", *("FAIL  " + b for b in bad)], summary
    return True, out + ["", "PASS  your run is genuine and your analysis matches your numbers."], summary


def main(argv):
    roster = get_roster(argv[0] if argv else None)
    ev = evidence_dir("s11")
    ok, lines, summary = check(ev, roster)
    print("\n".join(lines))
    if summary:
        save_json(os.path.join(ev, "pressure_check.json"), summary)
    if ok:
        print(f"\nsaved: {os.path.join(ev, 'pressure_check.json')}   (keep the whole evidence/s11 folder)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
