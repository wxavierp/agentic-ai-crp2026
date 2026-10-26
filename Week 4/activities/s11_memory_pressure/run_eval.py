"""
run_eval.py - run all 9 memory strategies against YOUR case with a REAL model and save the results.

    python run_eval.py                 # uses your .env (LLM_PROVIDER / LLM_MODEL / key, or a local Ollama model)
    python run_eval.py --workers 2     # fewer parallel calls (default 4)
    python run_eval.py --offline       # REHEARSAL ONLY: a stand-in "model" (the checker will not accept it)

Costs: 8 windows x 8 questions + 8 summary questions + 1 summary = 73 short calls. With gpt-4o-mini that is a few cents.
"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", ".."))
from common import get_roster, evidence_dir, save_json
import pressure_lib as L


def build_real_model():
    from utils.llm_client import LLMClient
    client = LLMClient()
    model = client._default_model()

    def ask(messages):
        return (client.chat(messages, temperature=0.0, max_tokens=80).text or "").strip()

    def summarize(prompt):
        return (client.chat([{"role": "user", "content": prompt}], temperature=0.0, max_tokens=300).text or "").strip()
    return ask, summarize, f"{client.provider}/{model}"


def main(argv):
    offline = "--offline" in argv
    workers, args, skip = 4, [], False
    for i, a in enumerate(argv):
        if skip:
            skip = False
        elif a == "--workers":
            workers, skip = int(argv[i + 1]), True
        elif not a.startswith("--"):
            args.append(a)
    roster = get_roster(args[0] if args else None)
    case = L.make_case(roster)
    if offline:
        m = L.OfflineModel(case)
        ask, summarize, model = m.ask, m.summarize, m.name
        print("OFFLINE stand-in: this is a rehearsal. Run again without --offline for the real thing.\n")
    else:
        try:
            ask, summarize, model = build_real_model()
        except Exception as e:
            sys.exit(f"Could not create the model client: {e}\nCheck your .env (OPENAI_API_KEY, or LLM_PROVIDER=ollama).")
    print(f"roster {roster}   case {case['hash']}   model {model}")
    t0 = time.time()
    try:
        strategies = L.run_strategies(case, ask, summarize, workers=workers)
    except Exception as e:
        sys.exit(f"\nThe model call failed: {e}\nNothing was saved. Fix the cause (key, network, model name) and run again.")
    results = {"version": 1, "roster": roster, "case_hash": case["hash"], "model": model,
               "seconds": round(time.time() - t0, 1), "strategies": strategies}
    results["seal"] = L.seal(case["hash"], results)
    ev = evidence_dir("s11")
    save_json(os.path.join(ev, "pressure_results.json"), results)
    grades = L.compute_grades(case, results)
    print("\n" + L.format_table(case, grades))
    want = L.smallest_window(grades)
    print("\nsmallest window that keeps >= 90%:", f"{want} turns" if want else "none of them")
    print(f"\nsaved: {os.path.join(ev, 'pressure_results.json')}")
    tmpl = os.path.join(ev, "pressure_analysis.json")
    if not os.path.exists(tmpl):
        save_json(tmpl, {
            "roster": roster,
            "smallest_window_turns": "FILL IN: a number from the table above, or \"none\"",
            "lost_facts": [{"fact": "F?", "strategy": "window-15", "why_code": "outside_window | dropped_by_summary | stale_value | model_error",
                            "why": "FILL IN: one sentence about YOUR numbers (which turn, which window)"}],
            "recommendation": "FILL IN (20+ words): which strategy for a support agent, and why - use your own numbers."})
        print(f"analysis template: {tmpl}   <- now do the analysis (see README), then:  python check.py")
    if offline:
        print("\n(offline rehearsal - the checker will not give credit for this run)")


if __name__ == "__main__":
    main(sys.argv[1:])
