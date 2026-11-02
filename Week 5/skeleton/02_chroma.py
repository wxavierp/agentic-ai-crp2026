"""
02 - Chroma: the same search, but Chroma keeps the text and the ids for you.

Chroma gives a DISTANCE (small = close). We turn it back into a score: score = 1 - distance.
You should get the same chunk ids and the same scores as in 01_faiss.py.

YOUR TASKS (2 TODOs, each has a HINT in the file)
  TODO 1  make a collection and add the chunks
  TODO 2  search it (score = 1 - distance)

Stuck?  trainer/02_chroma.py has the full version.

Then a search app opens in your browser (Gradio): type key terms and see the results.

Run:  python 02_chroma.py          (needs OPENAI_API_KEY in your .env)
"""
import os, sys, json
import numpy as np
import chromadb

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))          # Week 5/utils/llm_client.py is shared
from utils.llm_client import LLMClient

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))
client = LLMClient(provider="openai")


def embed(texts):
    return np.array(client.embed(texts), dtype="float32")


# ---- Step 1: make a collection and put the chunks in --------------------------------------------
# TODO 1 - open a Chroma database in this folder, make a collection, and put the chunks in.
# HINT:  db = chromadb.PersistentClient(path=os.path.join(HERE, "chroma_db"))
#        collection = db.get_or_create_collection("lumo", metadata={"hnsw:space": "cosine"})
#        collection.upsert(ids=[...ids...], documents=[...texts...], embeddings=embed([...texts...]).tolist())
#        (upsert = add, but safe to run twice. embeddings= stops Chroma from loading its own model.)
collection = None

if collection is None:
    sys.exit("TODO 1 is not done yet: open 02_chroma.py, find '# TODO 1', read the HINT.")
print("Step 1: the collection holds", collection.count(), "chunks")


# ---- Step 2: search ----------------------------------------------------------------------------
def search(question, k=3):
    # TODO 2 - ask the collection for the k closest chunks. Chroma gives a DISTANCE (small = close): score = 1 - distance.
    # HINT:  result = collection.query(query_embeddings=embed([question]).tolist(), n_results=k)
    #        ids = result["ids"][0]; distances = result["distances"][0]      # [0] = the answer for our one question
    #        return [(i, 1 - d) for i, d in zip(ids, distances)]
    return []


print("\nStep 2: search")
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


with gr.Blocks(title="Chroma search") as app:
    gr.Markdown("## Chroma search\nType a question or some key terms, then press Enter.")
    box = gr.Textbox(label="Search", placeholder="for example: refund, E-4210, warranty")
    table = gr.Dataframe(headers=["rank", "score", "chunk", "text"], wrap=True)
    box.submit(run_search, box, table)
    gr.Button("Search", variant="primary").click(run_search, box, table)
    gr.Examples(["Can I get my money back?", "E-4210", "How do I reset my password?", "Falcon S2 Pro warranty", "PN-30147"], inputs=box, fn=run_search, outputs=table, run_on_click=True)

app.launch()                                      # opens in your browser: http://127.0.0.1:7860
