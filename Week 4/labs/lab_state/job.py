"""
LAB 1 - The job that paid twice.

Run it:        python job.py
Start over:    python job.py --reset
Stretch:       python job.py --hard        (a nastier failure - read README.md first)

Only edit the parts marked  YOUR FIX.  Everything else is the lab itself.
"""
import os, random, sys

SUPPLIERS = [("Acme", 100), ("Beta", 250), ("Core", 80), ("Delta", 300), ("Echo", 60)]
TOTAL = sum(a for _, a in SUPPLIERS)            # 790
HARD = "--hard" in sys.argv

HERE = os.path.dirname(os.path.abspath(__file__))
def path(name):
    return os.path.join(HERE, name)
BANK, DONE_FILE, RUNS, FINISHED = path("bank.txt"), path("done.txt"), path(".runs"), path(".finished")


# ============================================================================
#  THE PRETEND BANK AND NETWORK  (do not edit - this is the lab, not your fix)
# ============================================================================
class NetworkError(Exception):
    pass

CRASH_AFTER = None          # set in main(): the network fails on this call number


def bank_lines():
    if not os.path.exists(BANK):
        return []
    return [l.rstrip("\n").split("|") for l in open(BANK) if l.strip()]

_calls = [0]
def bank_pay(name, amount, key=None):
    """Send money. A payment with a `key` that the bank has already seen is ignored (it will not pay twice)."""
    _calls[0] += 1
    failing = CRASH_AFTER is not None and _calls[0] == CRASH_AFTER
    if failing and not HARD:
        raise NetworkError("network error before paying " + name)       # nothing was sent
    if key and any(k == key for k, _, _ in bank_lines()):
        return "already processed"
    with open(BANK, "a") as f:
        f.write("%s|%s|%d\n" % (key or "", name, amount))
    if failing and HARD:
        raise NetworkError("network error AFTER paying " + name + " - the program never heard back")
    return "ok"


# ============================================================================
#  THE JOB  -  this is where YOUR FIX goes
# ============================================================================
def load_done():
    # YOUR FIX 1: read done.txt and return a set of the supplier names that are already paid.
    #             (If the file does not exist yet, return an empty set.)
    return set()


def mark_done(name):
    # YOUR FIX 2: write `name` on a new line at the end of done.txt, so a restart can see it.
    pass


def pay_all():
    done = load_done()
    for name, amount in SUPPLIERS:
        # YOUR FIX 3: if `name` is already in `done`, print "  skipped <name> (already paid)" and `continue`.
        bank_pay(name, amount)                       # STRETCH (--hard only): pass key="pay-" + name
        print("  paid %-6s %4d AED" % (name, amount))
        mark_done(name)


# ============================================================================
#  RUNNER  (do not edit)
# ============================================================================
def sent():
    names = {}
    for _, n, a in bank_lines():
        names.setdefault(n, []).append(int(a))
    return names, sum(int(a) for _, _, a in bank_lines())

def reset():
    for f in (BANK, DONE_FILE, RUNS, FINISHED):
        if os.path.exists(f):
            os.remove(f)
    print("Reset. The bank is empty and done.txt is gone.")

def main():
    global CRASH_AFTER
    if "--reset" in sys.argv:
        return reset()
    runs = int(open(RUNS).read()) if os.path.exists(RUNS) else 0
    open(RUNS, "w").write(str(runs + 1))
    was_finished = os.path.exists(FINISHED)
    total_when_finished = int(open(FINISHED).read()) if was_finished else None
    if runs < 2 and not was_finished:                # the first two runs hit a network failure at a random moment
        CRASH_AFTER = random.randint(2, 4)

    print("Paying %d suppliers..." % len(SUPPLIERS))
    try:
        pay_all()
    except NetworkError as e:
        print("  " + str(e) + " - the program stopped")
        names, total = sent()
        print("Bank: %d AED has left the account (the invoices add up to %d AED)." % (total, TOTAL))
        print("Run it again.")
        return
    print("  DONE - the job finished")
    names, total = sent()
    print("Bank: {:,} AED has left the account (the invoices add up to {} AED).".format(total, TOTAL))
    twice = ["%s x%d" % (n, len(v)) for n, v in names.items() if len(v) > 1]
    missing = [n for n, _ in SUPPLIERS if n not in names]
    ok1 = not twice and not missing
    ok2 = total == TOTAL
    print()
    print("CHECK 1  every supplier was paid exactly once ........ " + ("PASS" if ok1 else "FAIL  (" + ", ".join(twice + ["missing " + m for m in missing]) + ")"))
    print("CHECK 2  the total sent is %d AED ................... " % TOTAL + ("PASS" if ok2 else "FAIL  (%s AED)" % "{:,}".format(total)))
    if was_finished:
        ok3 = total == total_when_finished
        print("CHECK 3  running it again sends nothing more ......... " + ("PASS" if ok3 else "FAIL  (%d AED more went out)" % (total - total_when_finished)))
        if ok1 and ok2 and ok3:
            print("\nALL THREE CHECKS PASSED. Your job is safe to restart.")
        else:
            print("\nNot yet. Fix it, then:  python job.py --reset   and run it again until DONE, then once more.")
    else:
        open(FINISHED, "w").write(str(total))
        print("CHECK 3  running it again sends nothing more ......... run it ONE more time to find out")


if __name__ == "__main__":
    main()
