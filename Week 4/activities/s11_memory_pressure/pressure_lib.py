"""
pressure_lib.py - everything Activity 1 (Memory under pressure) shares: the case generator, the memory strategies,
the grader and the analysis validator.  Standalone: it does not use your project.

A CASE is a 40-turn conversation (one turn = a user message + the assistant's reply) between a user and a
travel-planning assistant.  Eight FACTS are hidden in it, at depths that depend on your roster number.
Each strategy decides what the model is allowed to SEE; then we ask 8 questions, one per fact, and grade the answers.
"""
import os, re, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from common import stable_hash

SALT = "s11-2026"
N_TURNS = 40
WINDOWS = [5, 10, 15, 20, 25, 30, 35, 40]      # the sweep: "last N turns"  (40 = the full history)
SUMMARY = "summary300+5"                       # everything older than the last 5 turns -> one <=300-token summary
THRESHOLD = 0.90                               # a strategy "keeps" the facts when its score is at least this
POINTS = {"exact": 1.0, "paraphrased": 1.0, "partial": 0.5, "absent": 0.0}
WHY_CODES = ("outside_window", "dropped_by_summary", "stale_value", "model_error")

SYSTEM = ("You are a travel-planning assistant. Answer the final question in one short sentence using ONLY what was said "
          "earlier in this conversation. If it was never said, answer exactly: I don't know.")

# --------------------------------------------------------------------------- value pools (a roster number picks from these)
SEATS = ["aisle", "window", "exit-row"]
WEEKDAYS = ["Friday", "Monday", "Sunday", "Thursday"]
DATES = [("14", "November"), ("3", "November"), ("21", "November"), ("9", "December"), ("18", "November"), ("27", "November"), ("5", "December"), ("12", "December")]
CITIES = ["Sharjah", "Ajman", "Fujairah", "Ras Al Khaimah", "Umm Al Quwain", "Al Ain", "Khor Fakkan", "Abu Dhabi"]
CURRENCIES = {"USD": ["US dollars", "US dollar", "dollars", "dollar", "US$"], "EUR": ["euro", "euros"], "GBP": ["pounds", "pound sterling", "sterling"],
              "INR": ["rupees", "Indian rupees"], "SAR": ["Saudi riyals", "Saudi riyal"], "QAR": ["Qatari riyals", "Qatari riyal"]}
COMPANIES = ["Nexora Labs", "Brightwell Group", "Kestrel Analytics", "Orbis Freight", "Lumina Health", "Vantora Systems", "Quillon Retail", "Halcyon Marine"]
TIERS = ["Bronze", "Silver", "Gold", "Platinum"]
NUMBER_WORDS = {5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen"}
ACKS = ["Noted.", "Got it.", "Understood.", "Okay, I will keep that in mind.", "Thanks, noted.", "Sure."]

# 36 neutral chat pairs - none may contain a digit, a month, a weekday, a pooled city/seat/currency/company/tier or a number word.
FILLER = [
 ("What kind of weather should we expect during the trip?", "It is usually warm and dry, so light clothes and a hat are a good idea."),
 ("Can you suggest some places to eat near the venue?", "There are plenty of cafes and restaurants within walking distance of most business hotels."),
 ("How long does it take to get from the airport to the city centre?", "Usually under an hour by taxi, a bit longer in heavy traffic."),
 ("Is it easy to get around without a car?", "Yes, the metro and taxis cover most areas, and ride-hailing apps work well."),
 ("Should we bring formal clothes?", "A smart jacket is enough for most sessions; evenings are relaxed."),
 ("What about travel insurance?", "It is worth having. Check that it covers delays and lost luggage."),
 ("Do we need visas?", "That depends on each traveller's passport, so check the official site for each person."),
 ("Is tap water safe to drink?", "It is safe, though many visitors prefer bottled water."),
 ("Any tips for avoiding jet lag?", "Get daylight early, drink water, and try to sleep on local time as soon as you land."),
 ("Which area is best for a quiet stay?", "Look for neighbourhoods near the water or large parks; they are calmer at night."),
 ("Can you recommend a good coffee place?", "Specialty cafes are easy to find; I can shortlist a few near wherever you stay."),
 ("What should I pack in my carry-on?", "Chargers, a power adapter, medication, and a change of clothes."),
 ("Are power sockets different there?", "Mostly the type with flat pins, so bring an adapter just in case."),
 ("How do I get a local SIM card?", "Airports and malls sell them; you will need your ID to activate one."),
 ("Is it okay to use my phone for maps?", "Yes. Download offline maps first in case the signal is weak."),
 ("What are the best souvenirs?", "Spices, sweets, perfume oils, and handmade textiles are all popular."),
 ("Is there a good time to visit the old quarter?", "Early morning, before the heat and the crowds."),
 ("Can we get a guide for a half-day tour?", "Yes, local operators offer guided tours that you can book in advance."),
 ("What is the dress code at the mosque?", "Cover shoulders and knees, and women usually cover their hair. Scarves are often provided."),
 ("Where can we watch the sunset?", "The beachfront and the tall observation decks are favourite spots."),
 ("Is it safe to walk at night?", "Generally very safe, though normal city precautions still apply."),
 ("Can you suggest a relaxing activity after the conference?", "A spa session or a sunset boat ride works well after a busy day."),
 ("What is the tipping custom?", "A small tip is common in restaurants if service is not already included."),
 ("Do restaurants take reservations?", "Most do, and it is wise to book for larger groups."),
 ("How early should we get to the airport?", "Arrive a good while before departure; the queues can be long at peak times."),
 ("Is there a baggage limit?", "It depends on the fare, so check the ticket rules before packing."),
 ("Can you remind me what a layover means?", "It is a short stop between connecting flights; a long one is called a stopover."),
 ("Which neighbourhood has the best street food?", "The older districts, where small family-run stalls open late."),
 ("Should I rent a car?", "Probably not for a city trip; parking is costly and taxis are plentiful."),
 ("What about colleagues who have dietary needs?", "Most restaurants label dishes clearly, and staff are used to special requests."),
 ("Can you summarise the safety tips so far?", "Keep valuables close, use licensed taxis, and share your itinerary with a colleague."),
 ("Is it worth buying a city pass?", "Only if you plan many attractions; otherwise single tickets cost less."),
 ("What time do shops close?", "Malls stay open late into the evening, often until midnight."),
 ("Are there family-friendly places for a free afternoon?", "Yes, parks, aquariums and interactive museums are good choices."),
 ("Do you have a tip for early flights?", "Pack the night before and arrange your ride in advance."),
 ("Can you suggest a packing checklist?", "I can: documents, chargers, medication, light clothing, and a reusable bottle."),
]

KINDS = ["preference", "constraint", "date", "number", "correction", "instruction", "identity", "stale"]   # F1..F8


def ordinal(n):
    n = int(n)
    return "%d%s" % (n, "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


# --------------------------------------------------------------------------- generator
def _facts(rng):
    seat = rng.choice(SEATS); day = rng.choice(WEEKDAYS); dd, mm = rng.choice(DATES)
    n = rng.choice([k for k in range(5, 15) if str(k) != dd])      # never the same number as the date
    old_c, new_c = rng.sample(CITIES, 2); cur = rng.choice(list(CURRENCIES)); comp = rng.choice(COMPANIES)
    old_t, new_t = (lambda i, j: (TIERS[i], TIERS[j]))(*sorted(rng.sample(range(len(TIERS)), 2)))
    mon = mm[:3]
    F = [
     dict(kind="preference", question="Which type of seat does the user prefer?", exact=seat, aliases=[seat + " seat", seat + " seats"],
          partial=[], stale=[], say=f"I always book an {seat} seat if I can." if seat[0] in "aeiou" else f"I always book a {seat} seat if I can."),
     dict(kind="constraint", question="Which weekday must be avoided for travel?", exact=day, aliases=[day + "s", day[:3]], partial=[], stale=[],
          say=f"Please avoid {day} for travel; nobody on the team can go that day."),
     dict(kind="date", question="When does the conference start?", exact=f"{dd} {mm}",
          aliases=[f"{mm} {dd}", f"{dd} {mon}", f"{mon} {dd}", f"{ordinal(dd)} {mm}", f"{mm} {ordinal(dd)}", f"{ordinal(dd)} of {mm}", f"{mon} {ordinal(dd)}", f"{dd}/{ {'November': 11, 'December': 12}[mm] }"],
          partial=[mm], stale=[], say=f"The conference starts on {dd} {mm}."),
     dict(kind="number", question="How many people are travelling?", exact=str(n), aliases=[NUMBER_WORDS[n]], partial=[], stale=[],
          say=f"There are {n} of us travelling in total."),
     dict(kind="correction", question="In which city will the hotel be?", exact=new_c, aliases=[], partial=[], stale=[old_c],
          say=f"Sorry, correction: the hotel should be in {new_c}, not {old_c}.", before=f"We will probably book the hotel in {old_c}."),
     dict(kind="instruction", question="Which currency should prices be quoted in?", exact=cur, aliases=CURRENCIES[cur], partial=[], stale=[],
          say=f"From now on, please quote all prices in {cur}."),
     dict(kind="identity", question="Which company does the user work for?", exact=comp, aliases=[], partial=[comp.split()[0]], stale=[],
          say=f"I work at {comp}, by the way."),
     dict(kind="stale", question="What is the user's current loyalty tier?", exact=new_t, aliases=[], partial=[], stale=[old_t],
          say=None, before=f"My loyalty tier is {old_t}.", user_final="Any update on my account?",
          assistant_final=f"[system note] Your loyalty tier was upgraded: it is now {new_t}."),
    ]
    return F


def make_case(roster):
    """Deterministic: the same roster number always gives the same case."""
    rng = random.Random(f"{SALT}-{int(roster)}")
    facts = _facts(rng)
    # where each final statement sits: the OLDEST is at turn p0 (12..28) so the window you need differs per student
    p0 = rng.randint(12, 28)
    last = rng.choice([38, 39, 40])
    others = rng.sample(range(p0 + 1, last), 6)
    positions = sorted([p0, last] + others)
    order = list(range(8)); rng.shuffle(order)
    used = set(positions)
    for slot, fi in zip(positions, order):
        facts[fi]["turn"] = slot
    for f in facts:                                  # an earlier turn carries the ORIGINAL value of a changing fact
        if "before" in f:
            near = [q for q in range(f["turn"] - 8, f["turn"] - 2) if q >= 2 and q not in used]
            anywhere = [q for q in range(2, f["turn"]) if q not in used]
            f["origin_turn"] = rng.choice(near or anywhere)
            used.add(f["origin_turn"])
    filler = rng.sample(FILLER, N_TURNS - len(used))
    turns, fi_iter = [], iter(filler)
    by_turn = {}
    for f in facts:
        by_turn[f["turn"]] = (f, "final")
        if "before" in f:
            by_turn[f["origin_turn"]] = (f, "before")
    for n in range(1, N_TURNS + 1):
        if n in by_turn:
            f, which = by_turn[n]
            if which == "before":
                u, a = f["before"], rng.choice(ACKS)
            elif f["kind"] == "stale":
                u, a = f["user_final"], f["assistant_final"]
            else:
                u, a = f["say"], rng.choice(ACKS)
        else:
            u, a = next(fi_iter)
        turns.append({"n": n, "user": u, "assistant": a})
    out_facts = []
    for i, f in enumerate(facts, 1):
        out_facts.append({"id": f"F{i}", "kind": f["kind"], "question": f["question"], "exact": f["exact"], "aliases": f["aliases"],
                          "partial": f["partial"], "stale": f["stale"], "turn": f["turn"], "origin_turn": f.get("origin_turn")})
    case = {"version": 1, "roster": int(roster), "turns": turns, "facts": out_facts}
    case["hash"] = stable_hash({"turns": turns, "facts": out_facts})
    return case


# --------------------------------------------------------------------------- grader
def _norm(s):
    return " " + re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip() + " "

def _has(answer_norm, phrase):
    p = _norm(phrase)
    return p.strip() != "" and p in answer_norm

NEGATED = re.compile(r"\b(?:not|instead of|rather than|previously|formerly|was|from|changed from|corrected from)\b(?:\s+\w+){0,2}\s+$")

def _stale_hit(answer, stale_values):
    """Does the answer present an OLD value as current?  'Ajman, not Sharjah' does not count."""
    low = " ".join(re.sub(r"[^a-z0-9 ]+", " ", answer.lower()).split())
    for s in stale_values:
        sl = " ".join(re.sub(r"[^a-z0-9 ]+", " ", s.lower()).split())
        for m in re.finditer(r"\b" + re.escape(sl) + r"\b", low):
            if not NEGATED.search(low[:m.start()]):
                return True
    return False

def grade(fact, answer):
    a = _norm(answer or "")
    stale = _stale_hit(answer or "", fact["stale"])
    exact = _has(a, fact["exact"]); alias = any(_has(a, x) for x in fact["aliases"]); part = any(_has(a, x) for x in fact["partial"])
    if stale and (exact or alias):
        level = "partial"                   # hedges between the old and the new value
    elif exact:
        level = "exact"
    elif alias:
        level = "paraphrased"
    elif stale:
        level = "absent"                    # gave the OLD value: wrong
    elif part:
        level = "partial"
    else:
        level = "absent"
    return {"level": level, "stale": stale}

def score(grades):
    return sum(POINTS[g["level"]] for g in grades.values()) / len(grades)

def compute_grades(case, results):
    out = {}
    for name, res in results["strategies"].items():
        g = {f["id"]: grade(f, res["answers"].get(f["id"], "")) for f in case["facts"]}
        out[name] = {"facts": g, "score": round(score(g), 4)}
    return out

def summary_has(fact, results):
    """Did the model's own summary keep this fact's (current) value?"""
    text = _norm(results["strategies"].get(SUMMARY, {}).get("summary_text", ""))
    return any(_has(text, v) for v in [fact["exact"]] + list(fact["aliases"]))

def seal(case_hash, results):
    """A fingerprint of the answers. It catches accidental edits to the results file (re-run instead of editing)."""
    body = {n: r["answers"] for n, r in sorted(results["strategies"].items())}
    body["summary"] = results["strategies"].get(SUMMARY, {}).get("summary_text", "")
    return stable_hash([SALT, case_hash, results.get("model"), body])

def window_of(name):
    return int(name.split("-")[1]) if name.startswith("window-") else None

def smallest_window(grades):
    for n in WINDOWS:
        key = f"window-{n}"
        if key in grades and grades[key]["score"] >= THRESHOLD:
            return n
    return None

def strategy_names():
    return [f"window-{n}" for n in WINDOWS] + [SUMMARY]


# --------------------------------------------------------------------------- what each strategy lets the model see
def _pairs(turns):
    msgs = []
    for t in turns:
        msgs += [{"role": "user", "content": t["user"]}, {"role": "assistant", "content": t["assistant"]}]
    return msgs

def window_messages(case, n, question):
    return [{"role": "system", "content": SYSTEM}] + _pairs(case["turns"][-n:]) + [{"role": "user", "content": question}]

def summary_messages(case, summary, question):
    return ([{"role": "system", "content": SYSTEM}, {"role": "system", "content": "Summary of the earlier conversation: " + summary}]
            + _pairs(case["turns"][-5:]) + [{"role": "user", "content": question}])

def summary_prompt(case):
    older = "\n".join(f"User: {t['user']}\nAssistant: {t['assistant']}" for t in case["turns"][:-5])
    return ("Summarize this conversation in at most 300 tokens (about 200 words). Be factual.\n\n" + older)


# --------------------------------------------------------------------------- running it
def run_strategies(case, ask, summarize, workers=4, progress=print):
    """ask(messages) -> answer text;  summarize(prompt) -> summary text.  Returns the results dict (answers only)."""
    from concurrent.futures import ThreadPoolExecutor
    progress("summarising the first 35 turns ...")
    summary_text = summarize(summary_prompt(case))
    jobs = []
    for n in WINDOWS:
        for f in case["facts"]:
            jobs.append((f"window-{n}", f["id"], window_messages(case, n, f["question"])))
    for f in case["facts"]:
        jobs.append((SUMMARY, f["id"], summary_messages(case, summary_text, f["question"])))
    done = [0]
    def work(job):
        name, fid, msgs = job
        ans = ask(msgs)
        done[0] += 1
        if done[0] % 8 == 0:
            progress(f"  {done[0]}/{len(jobs)} questions answered")
        return name, fid, ans
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        out = list(pool.map(work, jobs))
    strategies = {name: {"answers": {}} for name in strategy_names()}
    for name, fid, ans in out:
        strategies[name]["answers"][fid] = ans
    strategies[SUMMARY]["summary_text"] = summary_text
    return strategies


# --------------------------------------------------------------------------- offline stand-in (rehearsal + tests only)
class OfflineModel:
    """NOT a real model. It 'reads' the messages it is given and answers from them exactly, so the only thing that
    changes between strategies is what each one lets it SEE. Good for rehearsing; the checker refuses it for credit."""
    name = "offline-stand-in"

    def __init__(self, case):
        self.facts = {f["question"]: f for f in case["facts"]}

    def ask(self, messages):
        q = messages[-1]["content"]
        f = self.facts.get(q)
        if not f:
            return "I don't know."
        for m in reversed(messages[:-1]):
            if m["role"] == "system" and not m["content"].startswith("Summary"):
                continue
            if _has(_norm(m["content"]), f["exact"]):
                return f"It is {f['exact']}."
        return "I don't know."

    def summarize(self, prompt):
        user_lines = [l[6:] for l in prompt.split("\n") if l.startswith("User: ")]
        return " ".join(" ".join(l.split()[:7]) + "." for l in user_lines)


# --------------------------------------------------------------------------- the table students look at
SYMBOL = {"exact": "E", "paraphrased": "p", "partial": "~", "absent": "."}

def format_table(case, grades):
    ids = [f["id"] for f in case["facts"]]
    lines = ["strategy        " + " ".join(f"{i:>3}" for i in ids) + "   score",
             "-" * (16 + 4 * len(ids) + 9)]
    for name in strategy_names():
        if name not in grades:
            continue
        g = grades[name]
        cells = " ".join(" " + SYMBOL[g["facts"][i]["level"]] + ("*" if g["facts"][i]["stale"] else " ") for i in ids)
        mark = "  <- keeps >= 90%" if g["score"] >= THRESHOLD else ""
        lines.append(f"{name:<15} {cells}   {g['score'] * 100:5.1f}%{mark}")
    lines += ["", "E exact   p paraphrased   ~ partial   . absent   * an OLD value was given"]
    return "\n".join(lines)


# --------------------------------------------------------------------------- checking the student's analysis
def validate_analysis(case, results, grades, analysis):
    """-> list of problems (empty = the analysis is consistent with YOUR run)."""
    P = []
    want = smallest_window(grades)
    claim = analysis.get("smallest_window_turns")
    if want is None and claim not in ("none", None):
        P.append(f"smallest_window_turns: no window reached {int(THRESHOLD * 100)}% in your results, so the answer is \"none\"")
    elif want is not None and claim != want:
        P.append(f"smallest_window_turns: your results say {want} (the smallest window scoring >= {int(THRESHOLD * 100)}%), not {claim!r}")
    facts = {f["id"]: f for f in case["facts"]}
    lost = analysis.get("lost_facts") or []
    if len(lost) < 3:
        P.append("lost_facts: list at least 3 (fact, strategy) pairs that were NOT recalled fully")
    seen_s, seen_k = set(), set()
    for i, e in enumerate(lost, 1):
        fid, strat, code, why = e.get("fact"), e.get("strategy"), e.get("why_code"), str(e.get("why", ""))
        tag = f"lost_facts[{i}]"
        if fid not in facts:
            P.append(f"{tag}: unknown fact {fid!r}"); continue
        if strat not in grades:
            P.append(f"{tag}: unknown strategy {strat!r}"); continue
        g = grades[strat]["facts"][fid]
        if g["level"] in ("exact", "paraphrased"):
            P.append(f"{tag}: {fid} WAS recalled under {strat} in your results"); continue
        seen_s.add(strat); seen_k.add(facts[fid]["kind"])
        if code not in WHY_CODES:
            P.append(f"{tag}: why_code must be one of {', '.join(WHY_CODES)}"); continue
        n = window_of(strat)
        t = facts[fid]["turn"]
        in_summary_zone = strat == SUMMARY and t <= N_TURNS - 5
        if code == "outside_window":
            if not (n and t < N_TURNS + 1 - n):
                P.append(f"{tag}: {fid} (turn {t}) was INSIDE {strat}, so it cannot be 'outside_window'")
            elif str(t) not in re.findall(r"\d+", why):
                P.append(f"{tag}: say WHICH turn {fid} sits at and which turns {strat} can see - your reason should mention the number {t}")
        if code == "dropped_by_summary":
            if not in_summary_zone:
                P.append(f"{tag}: 'dropped_by_summary' needs the summary strategy and a fact older than the last 5 turns")
            elif summary_has(facts[fid], results):
                P.append(f"{tag}: your summary DID keep {fid}'s value (read summary_text in your results) - so what actually went wrong?")
            elif str(t) not in re.findall(r"\d+", why):
                P.append(f"{tag}: mention the turn number {t} where {fid} was said")
        if code == "stale_value" and not g["stale"]:
            P.append(f"{tag}: no OLD value appears in the answer for {fid} under {strat}")
        if code == "model_error":
            if (n and t < N_TURNS + 1 - n) or (in_summary_zone and not summary_has(facts[fid], results)):
                P.append(f"{tag}: the model could not see {fid} under {strat}; that is not a model error - was it outside the window / dropped by the summary?")
        if len(why.split()) < 8:
            P.append(f"{tag}: write the reason in at least 8 words")
    if len(seen_s) < 2:
        P.append("lost_facts: use at least 2 different strategies")
    if len(seen_k) < 2:
        P.append("lost_facts: use at least 2 different kinds of fact")
    if len(str(analysis.get("recommendation", "")).split()) < 20:
        P.append("recommendation: at least 20 words - which strategy would you use for a support agent, and why?")
    return P
