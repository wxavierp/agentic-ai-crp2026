# Week 5 - Vector stores and re-ranking  (Session 14, Mon 2 Nov)

**Learning objective:** store your document vectors in a vector store (FAISS and Chroma) and improve the top results with a re-ranking step.

```
Week 5/
  skeleton/    your files: fill in the TODOs, run them
    01_faiss.py     build, save, load and search a FAISS index      (3 TODOs)
    02_chroma.py    the same search with Chroma                      (2 TODOs)
    03_rerank.py    vector top 10, then re-rank with a keyword score (4 TODOs)
    data/           84 chunks and 10 test questions (ready-made)
  trainer/     the same files and folders with the finished code
  utils/       llm_client.py, the same client as Weeks 1-4 (now with embed()), shared by both
```

## Set up (once)

```
pip install numpy faiss-cpu chromadb gradio openai python-dotenv
```
Put `OPENAI_API_KEY` in the `.env` file at the repo root (the same one as Weeks 1-4). The labs use OpenAI `text-embedding-3-small`; a whole run costs a fraction of a cent.

## How to work

1. `cd "Week 5/skeleton"` and run `python 01_faiss.py`. It stops with "TODO 1 is not done yet": everything is connected.
2. Open the file, find `# TODO 1`, read the HINT, write the code, run it again. Then the next TODO, then the next file.
3. Stuck? Open the same file in `trainer/`.

When your TODOs work, each file opens a **search app in your browser** (Gradio, http://127.0.0.1:7860): type key terms or click an example and see the results. Press Ctrl+C in the terminal to stop it. In `03_rerank.py` the app shows vector search and re-ranked search side by side, with a slider for the weight.

What you should see in the terminal: `01_faiss.py` and `02_chroma.py` print the same chunk ids with the same scores. `03_rerank.py` prints that vector search alone finds 8 of 10, re-ranking finds 9 of 10, and a table of five weights.
One question to answer in the chat: **which question got worse when keywords counted more, and why?**
