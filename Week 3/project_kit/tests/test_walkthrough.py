"""Offline test for example_support_desk/walkthrough_reflect.py (scripted model, no key)."""
import sys, os, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "example_support_desk"))
import walkthrough_reflect as W

def run(*argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = W.main(list(argv))
    return out, buf.getvalue()

def test_planted_mistake_is_caught_then_confirmed():
    out, text = run("--offline")
    assert out["status"] == "confirmed" and out["rounds"] == 1
    assert "PLANTED MISTAKE" in text and "420" in text
    assert "the number 420 is in the answer but in no tool result" in text
    for step in ("STEP 1", "STEP 2", "STEP 3", "STEP 4", "STEP 5"):
        assert step in text
    assert text.index("STEP 3") < text.index("STEP 5") < text.index("STEP 4")      # verify, revise, then critic
    assert "get_order_status({'order_id': 'A100'}) -> A100: shipped, total 240 AED" in text   # evidence is printed
    assert "EVIDENCE (what the tools actually returned):" in text                     # and reaches the critic prompt

def test_no_plant_goes_straight_to_the_critic():
    out, text = run("--offline", "--no-plant")
    assert out["status"] == "confirmed" and out["rounds"] == 0 and "PLANTED" not in text.replace("PLANTED MISTAKE (", "")
    assert text.index("STEP 3") < text.index("STEP 4")

def test_plant_mistake_helper():
    assert W.plant_mistake("total 240 AED") == "total 420 AED"
    assert W.plant_mistake("total 11 AED") == "total 18 AED"       # swapping equal digits changes nothing -> +7
    assert "999" in W.plant_mistake("no digits here")

if __name__ == "__main__":
    n = 0
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v(); n += 1; print("ok", k)
    print(n, "passed")
