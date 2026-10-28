"""common.py - tiny helpers shared by every Week 4 activity and demo (standalone: not part of your project)."""
import os, sys, json, hashlib

WEEK4 = os.path.dirname(os.path.abspath(__file__))
if WEEK4 not in sys.path:
    sys.path.insert(0, WEEK4)          # so `from utils.llm_client import LLMClient` works from any sub-folder


def get_roster(arg=None, ask=input):
    """Your personal number (any whole number; it seeds your own data): from the command line, else the saved one, else asked ONCE and saved."""
    path = os.path.join(WEEK4, ".student_id")
    if arg is not None:
        n = int(arg)
    elif os.path.exists(path):
        n = int(open(path).read().strip())
    else:
        while True:
            try:
                n = int(ask("Your personal number (any whole number you will remember, e.g. 17 - it only makes YOUR data different from your classmates'): ").strip())
                break
            except ValueError:
                print("  numbers only, e.g. 17")
    with open(path, "w") as f:
        f.write(str(n))
    return n


def evidence_dir(session):
    """Where the results of an activity are saved: Week 4/evidence/<session>/ . Keep this folder."""
    d = os.path.join(WEEK4, "evidence", session)
    os.makedirs(d, exist_ok=True)
    return d


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


def save_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
