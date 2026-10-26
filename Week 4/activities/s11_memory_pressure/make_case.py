"""
make_case.py - build YOUR 40-turn conversation (same roster number -> same case, every time) and show where the 8 facts are.

    python make_case.py            # uses your saved roster number (asks once)
    python make_case.py 17         # or give it
    python make_case.py --show     # also print the whole conversation
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", ".."))
from common import get_roster, evidence_dir, save_json
import pressure_lib as L


def main(argv):
    show = "--show" in argv
    args = [a for a in argv if not a.startswith("--")]
    roster = get_roster(args[0] if args else None)
    case = L.make_case(roster)
    out = os.path.join(evidence_dir("s11"), "pressure_case.json")
    save_json(out, case)
    print(f"roster {roster}   case id {case['hash']}   saved to {out}\n")
    print("The 8 facts hidden in your conversation (the checker uses these; the model is NOT told them):")
    for f in case["facts"]:
        extra = f"   (the earlier, OLD value was said at turn {f['origin_turn']})" if f["origin_turn"] else ""
        print(f"  {f['id']}  {f['kind']:<11} said at turn {f['turn']:>2}   Q: {f['question']}{extra}")
    if show:
        print("\n--- the conversation ---")
        for t in case["turns"]:
            print(f"[{t['n']:>2}] user: {t['user']}\n     asst: {t['assistant']}")
    print("\nNext:  python run_eval.py")


if __name__ == "__main__":
    main(sys.argv[1:])
