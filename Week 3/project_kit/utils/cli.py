"""
Tiny helper so demos ask YOU for a goal instead of hard-coding one.

    from utils.cli import ask_goal
    goal = ask_goal(["first suggestion", "second suggestion"])

Shows the suggestions, then waits:
    - type 1 or 2  -> use that suggestion
    - type your own goal -> use it
    - just press Enter -> use suggestion 1
If there is no keyboard (piped input / CI), it quietly uses suggestion 1.
"""
import sys


def ask_goal(suggestions, prompt="Your goal"):
    print("\nSuggested goals to try:")
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}) {s}")
    try:
        raw = input(f"\n{prompt} - type 1-{len(suggestions)}, write your own, or press Enter for 1: ").strip()
    except EOFError:
        raw = ""
    if not raw:
        goal = suggestions[0]
    elif raw.isdigit() and 1 <= int(raw) <= len(suggestions):
        goal = suggestions[int(raw) - 1]
    else:
        goal = raw
    print(f"\nGOAL: {goal}\n")
    return goal


def converse(run_fn, suggestions, prompt="Your goal"):
    """
    A small chat loop around any agent.  run_fn(text) -> answer text.
    After each answer you can REPLY (answer the agent's question, ask a follow-up, or give a
    new goal).  The agent sees the conversation so far.  Press Enter on its own to finish.
    Returns a list of (user_message, answer).
    """
    history = []
    goal = ask_goal(suggestions, prompt)
    while True:
        if history:
            past = "\n".join(f"User: {u}\nAgent: {a}" for u, a in history)
            full = (f"Conversation so far:\n{past}\n\nUser's new message: {goal}\n"
                    "Continue helping. Use the earlier messages for context.")
        else:
            full = goal
        answer = run_fn(full)
        history.append((goal, str(answer)))
        try:
            reply = input("\nReply / follow-up / new goal (press Enter to finish): ").strip()
        except EOFError:
            reply = ""
        if not reply:
            print("\nSession finished.")
            return history
        print(f"\nYOU: {reply}\n")
        goal = reply
