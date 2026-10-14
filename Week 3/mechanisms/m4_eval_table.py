"""
Mechanism 4 - reading an eval table and choosing by evidence.
No API key. Run:  python mechanisms/m4_eval_table.py

Recorded results of 3 variants on the same 5 golden tasks: (passed 1/0, model calls used).
Reflection adds ~2 extra model calls per task (critic + possible revise).
"""
RESULTS = {
    "A  ReAct only":        {"G1": (1, 2), "G2": (1, 3), "G3": (0, 8), "G4": (1, 2), "G5": (0, 3)},
    "B  + planner":         {"G1": (1, 4), "G2": (1, 5), "G3": (1, 7), "G4": (1, 4), "G5": (0, 5)},
    "C  + planner + reflect": {"G1": (1, 6), "G2": (1, 7), "G3": (1, 9), "G4": (1, 6), "G5": (1, 7)},
}
print(f"{'variant':26s}{'pass':>6s}{'avg calls':>11s}{'calls / pass':>14s}   failed")
for name, res in RESULTS.items():
    passed = sum(p for p, _ in res.values())
    calls = sum(c for _, c in res.values())
    failed = [t for t, (p, _) in res.items() if not p]
    print(f"{name:26s}{passed:>4d}/5{calls / 5:>11.1f}{calls / passed:>14.1f}   {failed}")

print("\nQUESTIONS (argue it, then decide):")
print("  1. C passes everything - but what is its calls/pass versus A? Is 'ship C' obvious?")
print("  2. G3 and G5 flip between variants. What does each flip tell you about WHY the layer helped?")
print("  3. Your project handles refunds (risky). Does that change which variant you ship?")
print("  4. 5 tasks, 1 run each. What would make you trust this table more?")
