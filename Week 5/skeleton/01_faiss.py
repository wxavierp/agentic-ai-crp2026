"""
01 - FAISS: build an index, save it, load it, search it.

FAISS keeps ONLY the vectors. It answers "row 7", and YOUR list says what row 7 is (chunks[7]).

YOUR TASKS (3 TODOs, each has a HINT in the file)
  TODO 1  make the index and add the vectors
  TODO 2  save it and load it back
  TODO 3  search it

Stuck?  trainer/01_faiss.py has the full version.

Then a search app opens in your browser (Gradio): type key terms and see the results.

Run:  python 01_faiss.py          (needs OPENAI_API_KEY in your .env)
"""
import os, sys, json
import numpy as np
import faiss

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))          # Week 5/utils/llm_client.py is shared
from utils.llm_client import LLMClient

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))      # [{"id": ..., "text": ...}, ...]
client = LLMClient(provider="openai")
INDEX_FILE = os.path.join(HERE, "chunks.faiss")


def embed(texts):
    """texts in, a float32 matrix out (one row per text, 1536 numbers each)."""
    return np.array(client.embed(texts), dtype="float32")


# ---- Step 1: build the index -------------------------------------------------------------------
vectors = embed([c["text"] for c in chunks])

# TODO 1 - make the index and put the vectors in.
# HINT:  faiss.normalize_L2(vectors)                    # scale every row to length 1 (then inner product = cosine)
#        index = faiss.IndexFlatIP(vectors.shape[1])    # IP = inner product; Flat = compare with every vector
#        index.add(vectors)
index = None

if index is None:
    sys.exit("TODO 1 is not done yet: open 01_faiss.py, find '# TODO 1', read the HINT.")
print("Step 1: the index holds", index.ntotal, "vectors")

# ---- Step 2: save it, load it back -------------------------------------------------------------
# TODO 2 - save the index to INDEX_FILE, then load it back into `index`.
# HINT:  faiss.write_index(index, INDEX_FILE)
#        index = faiss.read_index(INDEX_FILE)

print("Step 2: saved and loaded again:", index.ntotal, "vectors")


# ---- Step 3: search ----------------------------------------------------------------------------
def search(question, k=3):
    # TODO 3 - embed the question, scale it to length 1, ask the index for the k best rows.
    # HINT:  q = embed([question])
    #        faiss.normalize_L2(q)
    #        scores, rows = index.search(q, k)       # scores FIRST, row numbers SECOND (both have one line per question: use scores[0], rows[0])
    #        row r means chunks[r]: return [(chunks[r]["id"], float(s)) for s, r in zip(scores[0], rows[0])]
    return []


print("\nStep 3: search")
for question in ["Can I get my money back?", "How do I reset my password?", "What is the warranty on the Falcon S2 Pro?"]:
    print(" ", question)
    for chunk_id, score in search(question):
        print("     %.2f  %s" % (score, chunk_id))


# ---- The search app (ready for you: nothing to fill in here) ------------------------------------
import gradio as gr

TEXT = {c["id"]: c["text"] for c in chunks}


def run_search(question):
    if not question.strip():
        return []
    return [[rank, round(score, 2), chunk_id, TEXT[chunk_id]] for rank, (chunk_id, score) in enumerate(search(question, 5), 1)]


with gr.Blocks(title="FAISS search") as app:
    gr.Markdown("## FAISS search\nType a question or some key terms, then press Enter.")
    box = gr.Textbox(label="Search", placeholder="for example: refund, E-4210, warranty")
    table = gr.Dataframe(headers=["rank", "score", "chunk", "text"], wrap=True)
    box.submit(run_search, box, table)
    gr.Button("Search", variant="primary").click(run_search, box, table)
    gr.Examples(["Can I get my money back?", "E-4210", "How do I reset my password?", "Falcon S2 Pro warranty", "PN-30147"], inputs=box, fn=run_search, outputs=table, run_on_click=True)

app.launch()                                      # opens in your browser: http://127.0.0.1:7860
