# Lab 1 - The job that paid twice  (30 minutes)

**You will be able to:** make a job safe to restart, so that an interruption never makes it repeat what it already did.

You need only Python 3 and this folder. No key, no installs, no other files.
Check that Python works: `python job.py --reset` (if `python` is not found, try `python3`).

## 1. Run it (5 min)
```
python job.py
```
The first runs hit a pretend network failure at a random moment. **Keep running `python job.py` until it says DONE**, then run it **one more time**.

Read the output. Find the line that starts `Bank:`.

## 2. Write one sentence (2 min)
On paper or in a comment: **What went wrong, and why did it happen?**
Hint: what does the program know when you start it again?

## 3. Fix it (15 min)
Open `job.py`. Edit only the places marked `YOUR FIX` (about 8 lines in all):
1. `load_done()` - read `done.txt` and return the supplier names already paid
2. `mark_done()` - write a supplier's name into `done.txt`
3. `pay_all()` - skip any supplier that is already in that list

## 4. Run it again (5 min)
```
python job.py --reset
python job.py        # again and again until DONE
python job.py        # one more time
```
The network fails at a different moment each time - you can't memorise where.
**Verify that all three checks pass:**
- CHECK 1 every supplier was paid exactly once
- CHECK 2 the total sent is 790 AED
- CHECK 3 running it again sends nothing more

## 5. Write one sentence (3 min)
**What did I learn?** (Say it so a friend who does not code would understand.)

## Stretch - if you finish early
```
python job.py --reset
python job.py --hard
```
This time the network fails *after* the money was sent, so the program never hears back. Is your fix still enough? Look at the `STRETCH` comment in `pay_all()` and at the `key` argument of `bank_pay()`.

## Keep it
Keep `job.py` as it is - in the last block of the session you will bring the same idea into your own project.
