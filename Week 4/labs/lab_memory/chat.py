"""
LAB 2 - The chatbot that forgets.

Chat with it:     python chat.py
Run the card for you and show PASS/FAIL:   python chat.py --check
Delete saved facts:                        python chat.py --reset
Use a real model instead of the stand-in:  python chat.py --real     (needs: pip install openai, and OPENAI_API_KEY)

The stand-in is NOT a model: it only answers from what the program sends it, so what you see is
exactly what your memory code did.  Only edit the parts marked  YOUR FIX.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FACTS_FILE = os.path.join(HERE, "facts.json")
SYSTEM = "You are a friendly assistant. Use what you know about the user."

# ============================================================================
#  YOUR FIX  - the bot's memory
# ============================================================================
WINDOW = 2          # YOUR FIX 1: how many recent exchanges (you + bot) the bot can see. Try 20.

HISTORY = []        # the conversation so far: [(what you said, what the bot said), ...]. Lives only while the program runs.


def load_facts():
    """Return the saved facts as a dict, like {"name": "Amira", "contact": "phone"}."""
    # YOUR FIX 2: read FACTS_FILE (JSON). If the file does not exist yet, return {}.
    return {}


def save_fact(slot, value):
    """Remember value under slot. A new value for the same slot must REPLACE the old one."""
    # YOUR FIX 3: load the facts, set facts[slot] = value, write them back to FACTS_FILE as JSON.
    pass


def forget_fact(slot):
    """Forget what we know under slot - really forget it."""
    # YOUR FIX 4: remove the slot from the saved facts (and save the file) ...
    #   ... and think: where else could the bot still find it?  (Hint: look at HISTORY.)
    pass


# ============================================================================
#  THE BOT  (do not edit)
# ============================================================================
def extract_facts(text):
    """A simple rule that spots facts in what you say. (In a real agent the MODEL calls a 'remember' tool.)"""
    text = text.replace("’", "'")
    found = []
    m = re.search(r"\b(?i:I'm|I am|my name is)\s+([A-Z][a-z]+)", text)
    if m:
        found.append(("name", m.group(1)))
    m = re.search(r"\bprefer\s+(?:to be contacted by\s+)?(email|phone|sms|whatsapp)", text, re.I)
    if m:
        found.append(("contact", m.group(1).lower()))
    m = re.search(r"\b(email|phone|sms|whatsapp)\s+from now on", text, re.I)
    if m:
        found.append(("contact", m.group(1).lower()))
    return found


def build_messages(user_text):
    """Exactly what the model gets on this turn."""
    msgs = [{"role": "system", "content": SYSTEM}]
    facts = load_facts()
    if facts:
        msgs.append({"role": "system", "content": "Known facts about the user:\n" + "\n".join("- %s: %s" % kv for kv in facts.items())})
    for u, b in HISTORY[-WINDOW:]:
        msgs.append({"role": "user", "content": u})
        msgs.append({"role": "assistant", "content": b})
    msgs.append({"role": "user", "content": user_text})
    return msgs


def standin(msgs):
    """Not a model: answers ONLY from the messages it is sent."""
    q = msgs[-1]["content"].lower()
    known = {}
    for m in msgs:                                         # earlier things the user said (oldest first, newest wins)
        if m["role"] == "user" and m is not msgs[-1]:
            for slot, value in extract_facts(m["content"]):
                known[slot] = value
    for m in msgs:                                         # saved facts win over chat history
        if m["role"] == "system" and m["content"].startswith("Known facts"):
            for slot, value in re.findall(r"^- (\w+): (.+)$", m["content"], re.M):
                known[slot] = value
    if "name" in q and "?" in q:
        return "Your name is %s." % known["name"] if "name" in known else "I don't know your name."
    if "contact" in q and "?" in q:
        return "I will contact you by %s." % known["contact"] if "contact" in known else "I don't know how you like to be contacted."
    return "Got it." if extract_facts(msgs[-1]["content"]) else "OK."


def ask_real(msgs):
    from openai import OpenAI
    r = OpenAI().chat.completions.create(model=os.environ.get("LLM_MODEL", "gpt-4o-mini"), messages=msgs, temperature=0)
    return r.choices[0].message.content


REAL = "--real" in sys.argv

def turn(user_text, quiet=False):
    forget = re.search(r"\bforget my (\w+)", user_text, re.I)
    if forget:
        forget_fact(forget.group(1).lower())
        reply = "Okay, I have forgotten your %s." % forget.group(1).lower()
        seen = None
    else:
        msgs = build_messages(user_text)
        reply = ask_real(msgs) if REAL else standin(msgs)
        seen = "[the bot could see: %d recent exchange(s) and %d saved fact(s)]" % (len(HISTORY[-WINDOW:]), len(load_facts()))
        for slot, value in extract_facts(user_text):
            save_fact(slot, value)
    HISTORY.append((user_text, reply))
    if not quiet:
        print("Bot: " + reply)
        if seen:
            print("     " + seen)
    return reply


def reset():
    if os.path.exists(FACTS_FILE):
        os.remove(FACTS_FILE)
    print("Saved facts deleted.")


def check():
    reset()
    HISTORY.clear()
    for t in ["Hi, I'm Amira.", "I prefer email.", "Tell me a joke.", "What can you do?", "Thanks.", "Actually, phone from now on."]:
        turn(t, quiet=True)
    c1 = "amira" in turn("What's my name?", quiet=True).lower()
    r = turn("How should you contact me?", quiet=True).lower()
    c2 = "phone" in r and "email" not in r
    HISTORY.clear()                                        # --- the program is closed and started again ---
    c3 = "amira" in turn("What's my name?", quiet=True).lower()
    r = turn("How should you contact me?", quiet=True).lower()
    c4 = "phone" in r
    turn("My name is Amira, by the way.", quiet=True)      # (so the name is in this conversation again)
    turn("forget my name", quiet=True)
    c5 = c3 and "amira" not in turn("What's my name?", quiet=True).lower()
    HISTORY.clear()                                        # --- closed and started again ---
    c6 = c3 and "amira" not in turn("What's my name?", quiet=True).lower()
    rows = [("remembers the name after 5 more turns", c1), ("uses the LATEST contact preference (phone, not email)", c2),
            ("after a restart: still knows the name", c3), ("after a restart: still knows the contact preference", c4),
            ("after 'forget my name': no longer knows it", c5), ("after 'forget my name' and a restart: still doesn't know it", c6)]
    print("")
    for i, (label, ok) in enumerate(rows, 1):
        print("CHECK %d  %-62s %s" % (i, label, "PASS" if ok else "FAIL"))
    print("")
    print("ALL CHECKS PASSED" if all(ok for _, ok in rows) else "Not yet - read the FAIL lines, fix, and run  python chat.py --check  again.")
    return all(ok for _, ok in rows)


def main():
    if "--reset" in sys.argv:
        return reset()
    if "--check" in sys.argv:
        return check()
    print("Chat with the bot. Press Enter on an empty line to quit.  (Say 'forget my name' to test forgetting.)")
    while True:
        try:
            text = input("\nYou: ").strip()
        except EOFError:
            break
        if not text:
            break
        turn(text)


if __name__ == "__main__":
    main()
