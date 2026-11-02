"""
03 - Re-rank: vector search first, then a keyword score on the top 10.

Vector search is good at MEANING and weak at exact codes (E-4210 looks like E-4021).
Keywords are the opposite. So we search in two steps:
    step 1  vector search       -> the 10 best candidates
    step 2  re-rank the 10      -> mixed = (1 - weight) * vector score + weight * keyword score
weight = 0 means ignore keywords, 1 means only keywords.

recall@3 = in how many of the 10 test questions is the right chunk in the top 3?

YOUR TASKS (4 TODOs, each has a HINT in the file)
  TODO 1  recall_at_3: count the questions where the right chunk is in the top 3
  TODO 2  keyword_score
  TODO 3  rerank
  TODO 4  try five weights

Stuck?  trainer/03_rerank.py has the full version.

Then a search app opens in your browser (Gradio): type key terms and see the results.

Run:  python 03_rerank.py          (needs OPENAI_API_KEY in your .env)
"""
import os, sys, json, re
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))          # Week 5/utils/llm_client.py is shared
from utils.llm_client import LLMClient

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))
questions = json.load(open(os.path.join(HERE, "data", "questions.json")))    # [{"question":..., "answer": chunk id}]
client = LLMClient(provider="openai")
IDS = [c["id"] for c in chunks]
TEXT = {c["id"]: c["text"] for c in chunks}

vectors = np.array(client.embed([c["text"] for c in chunks]))
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

STOP = set("a an the is are was were be been to of in on for and or it its my i me do does did can could how what when where "
           "which who whom with at by from this that there their your you we our if as will would should may might any some "
           "up out so than then them they he she his her us have has had get got".split())


def words(text):
    """The important words of a text (small words like 'the' are dropped)."""
    return [w for w in re.findall(r"[a-z0-9]+", text.lower().replace("-", " ")) if w not in STOP]


def vector_search(question, k=10):
    """Step 1 (ready for you): the k closest chunks as [(chunk id, vector score), ...], best first."""
    q = np.array(client.embed(question)[0])
    q /= np.linalg.norm(q)
    scores = vectors @ q
    return [(IDS[i], float(scores[i])) for i in np.argsort(-scores)[:k]]


def vector_only(question):
    return [chunk_id for chunk_id, _ in vector_search(question, len(IDS))]     # all chunks, best first


# ---- TODO 1: the measure ---------------------------------------------------------------------
def recall_at_3(search):
    """search(question) returns chunk ids, best first. Count the questions whose right chunk is in the top 3."""
    # TODO 1 - count the hits. A question is a HIT when its right chunk (item["answer"]) is in the first 3 ids.
    # HINT:  hits = 0
    #        for item in questions:
    #            if item["answer"] in search(item["question"])[:3]:
    #                hits += 1
    #        return hits
    return 0


print("Step 1: vector search alone finds", recall_at_3(vector_only), "of 10")
for item in questions:
    ids = vector_only(item["question"])
    if item["answer"] not in ids[:3]:
        print("   MISS (rank %d): %s" % (ids.index(item["answer"]) + 1, item["question"]))


# ---- TODO 2: the keyword score ---------------------------------------------------------------
def keyword_score(question, text):
    """The share of the question's words that are also in the text: 0 to 1."""
    # TODO 2 - the share of the question's words that are also in the text.
    # HINT:  q = set(words(question))        # set() removes repeats
    #        t = set(words(text))
    #        return len(q & t) / len(q)      # q & t = the words in BOTH. Example: 'falcon s2 warranty', text has falcon and s2 -> 2 of 3 -> 0.67
    return 0


print("\nStep 2: keyword_score('falcon s2 warranty', ...)")
print("   Falcon S2 warranty chunk:", round(keyword_score("falcon s2 warranty", TEXT["falcon-s2-warranty"]), 2))
print("   Orion X3 battery chunk:  ", round(keyword_score("falcon s2 warranty", TEXT["orion-x3-battery"]), 2))


# ---- TODO 3: re-rank -------------------------------------------------------------------------
def rerank(question, weight=0.25, candidates=10):
    """Step 1 + step 2. Return chunk ids, best first."""
    # TODO 3 - take the candidates from vector_search, give each a mixed score, sort, return the ids.
    # HINT:  found = vector_search(question, candidates)               # [(chunk id, vector score), ...]
    #        scored = []
    #        for chunk_id, vector_score in found:
    #            mixed = (1 - weight) * vector_score + weight * keyword_score(question, TEXT[chunk_id])
    #            scored.append((mixed, chunk_id))
    #        scored.sort(reverse=True)                                  # biggest mixed score first
    #        return [chunk_id for _, chunk_id in scored]
    return vector_only(question)


print("\nStep 3: re-ranked (weight 0.25) finds", recall_at_3(rerank), "of 10")
for item in questions:
    before = item["answer"] in vector_only(item["question"])[:3]
    after = item["answer"] in rerank(item["question"])[:3]
    if before != after:
        print("   %s -> %s   %s" % ("hit " if before else "MISS", "hit " if after else "MISS", item["question"]))


# ---- TODO 4: which weight is best? -----------------------------------------------------------
print("\nStep 4: weight on keywords | hits in top 3")
# TODO 4 - for each weight, count the hits and print one line.
# HINT:  for weight in [0, 0.25, 0.5, 0.75, 1.0]:
#            hits = recall_at_3(lambda question: rerank(question, weight))      # lambda = a tiny function with the weight filled in
#            print("   %.2f  |  %d of 10" % (weight, hits))

# Think about it, then answer in the chat (one sentence):
#   Which question got WORSE when keywords counted more, and why?


# ---- The search app (ready for you: nothing to fill in here) ------------------------------------
import gradio as gr


def run_search(question, weight):
    if not question.strip():
        return [], []
    vector_rows = [[rank, chunk_id, TEXT[chunk_id]] for rank, chunk_id in enumerate(vector_only(question)[:5], 1)]
    rerank_rows = [[rank, chunk_id, TEXT[chunk_id]] for rank, chunk_id in enumerate(rerank(question, weight)[:5], 1)]
    return vector_rows, rerank_rows


with gr.Blocks(title="Re-rank search") as app:
    gr.Markdown("## Vector search vs re-ranked search\nType a question or some key terms, then press Enter. Move the slider to change how much the keywords count.")
    box = gr.Textbox(label="Search", placeholder="for example: refund, E-4210, PN-30147")
    weight = gr.Slider(0, 1, value=0.25, step=0.05, label="weight on keywords (0 = vector only, 1 = keywords only)")
    with gr.Row():
        vector_table = gr.Dataframe(headers=["rank", "chunk", "text"], label="Step 1: vector search only", wrap=True)
        rerank_table = gr.Dataframe(headers=["rank", "chunk", "text"], label="Step 2: after re-ranking", wrap=True)
    box.submit(run_search, [box, weight], [vector_table, rerank_table])
    weight.change(run_search, [box, weight], [vector_table, rerank_table])
    gr.Button("Search", variant="primary").click(run_search, [box, weight], [vector_table, rerank_table])
    gr.Examples(["Can I get my money back?", "E-4210", "How do I reset my password?", "Falcon S2 Pro warranty", "PN-30147"], inputs=box)

app.launch()                                      # opens in your browser: http://127.0.0.1:7860
