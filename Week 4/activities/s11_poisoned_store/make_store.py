"""
make_store.py - build YOUR memory file (same roster number -> same file) and print it.

    python make_store.py            # uses your saved roster number (asks once)
    python make_store.py 17

The file is saved as evidence/s11/store.json. It holds 17 entries. SOME OF THEM ARE BAD.
Read the rules at the top of poison_lib.py, or in README.md - they are the only definition of "bad" used here.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", ".."))
from common import get_roster, evidence_dir, save_json
import poison_lib as L


def main(argv):
    roster = get_roster(argv[0] if argv else None)
    store = L.make_store(roster)
    path = os.path.join(evidence_dir("s11"), "store.json")
    save_json(path, L.public_store(store))
    print(f"roster {roster}  you are user {store['me']}   today = {store['now']}   file {store['hash']}   saved to {path}\n")
    print(f"{'id':<4} {'slot':<18} {'value':<58} {'source':<9} {'conf':<5} {'saved':<11} {'expires':<11} scope")
    for e in store["entries"]:
        print(f"{e['id']:<4} {e['slot']:<18} {e['value'][:56]:<58} {e['source']:<9} {str(e['confirmed']):<5} {e['ts']:<11} {str(e['expires'] or '-'):<11} {e['scope']}")
    print("\nNext:  python ablate.py")


if __name__ == "__main__":
    main(sys.argv[1:])
