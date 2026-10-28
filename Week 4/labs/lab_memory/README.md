# Lab 2 - The chatbot that forgets  (30 minutes)

**You will be able to:** tell the difference between a chat's *recent history* and saved *memory*, and make a bot that remembers, updates and forgets properly.

You need only Python 3 and this folder. No key, no installs. The bot runs on a stand-in that answers
**only from what the program sends it** - so what you see is exactly what your memory code did.
Check that Python works: `python chat.py --reset` (if `python` is not found, try `python3`).

## 1. Chat with it - type this card, one line at a time (8 min)
```
python chat.py
```
**Part A - one conversation**
```
Hi, I'm Amira.
I prefer email.
Tell me a joke.
What can you do?
Thanks.
Actually, phone from now on.
What's my name?               <- right answer: Amira
How should you contact me?    <- right answer: phone (not email)
```
Press Enter on an empty line to quit. Start it again (this is a restart):
```
python chat.py
What's my name?               <- right answer: Amira
How should you contact me?    <- right answer: phone
My name is Amira, by the way.
forget my name
What's my name?               <- right answer: I don't know
```
Quit, start it again, and ask `What's my name?` once more. <- right answer: I don't know

After every reply the bot prints what it could see: `[the bot could see: 2 recent exchange(s) and 0 saved fact(s)]`.

## 2. Write one sentence (2 min)
**Which lines gave the wrong answer, and what do you think is missing?**

## 3. Fix it (12 min)
Open `chat.py`. Edit only the places marked `YOUR FIX` (about 15 lines):
1. `WINDOW` - how many recent exchanges the bot can see
2. `load_facts()` - read `facts.json`
3. `save_fact()` - write a fact; a new value for the same slot must **replace** the old one
4. `forget_fact()` - really forget. Ask yourself: *where else could the bot still find it?*

## 4. Verify (5 min)
```
python chat.py --check
```
This types the card for you. **Verify that each check passes:**
1. remembers the name after 5 more turns
2. uses the latest contact preference (phone, not email)
3. after a restart: still knows the name
4. after a restart: still knows the contact preference
5. after "forget my name": no longer knows it
6. after "forget my name" and a restart: still doesn't know it

Then type the card by hand once more and watch the `[the bot could see ...]` lines.

## 5. Write one sentence (3 min)
**What did I learn?** In particular: why does making the window bigger *not* solve a restart?

## Keep it
Keep `chat.py` as it is - in the last block you bring the same ideas into your own project.
