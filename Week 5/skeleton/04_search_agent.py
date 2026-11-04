"""
04 - A search agent: it decides WHEN to search, and answers only from what it finds.

Plain RAG searches for every question. An agent decides: "Hi!" needs no search, "What is the warranty on
the Falcon S2 Pro?" does, and a two-part question needs two searches. If nothing useful comes back, it
must say "I don't know" instead of inventing an answer.

Run:  python 04_search_agent.py          (needs OPENAI_API_KEY in your .env)
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))          # Week 5/utils is shared
from utils.llm_client import LLMClient
from utils.kb_search import KnowledgeBase

chunks = json.load(open(os.path.join(HERE, "data", "chunks.json")))
kb = KnowledgeBase(chunks)                          # the Day 14 search: vector top 10, then keyword re-rank
client = LLMClient()                                # the chat model from your .env (LLM_PROVIDER)

# ---- TODO 1: the tool the model can call -------------------------------------------------------
# TODO 1 - describe the tool, so the model knows it exists and how to call it.
# HINT:  SEARCH_TOOL = {"type": "function",
#                       "function": {"name": "search_knowledge",
#                                    "description": "...when should the model use it? what does it return?...",
#                                    "parameters": {"type": "object",
#                                                   "properties": {"query": {"type": "string", "description": "what to look for"}},
#                                                   "required": ["query"]}}}
SEARCH_TOOL = None

if SEARCH_TOOL is None:
    sys.exit("TODO 1 is not done yet: open 04_search_agent.py, find '# TODO 1', read the HINT.")

# ---- TODO 3: the rules the agent must follow ---------------------------------------------------
# TODO 3 - write the rules. Add five rules to this prompt, in your own words:
# HINT:  1  use the search tool for facts about products, codes, parts, policies; answer greetings directly
#        2  if a question has two parts, search for each part
#        3  answer ONLY from the search results, and cite the id of the source after every fact, like [err-4210]
#        4  if the results do not contain the answer, say exactly: I don't know
#        5  SCOPE: you only talk about Lumo. For anything else (general knowledge, other shops, opinions) do not search
#           and do not answer: say exactly: I can only help with questions about Lumo products and policies
SYSTEM = "You are the support assistant of the Lumo shop."


# ---- TODO 2: the agent loop --------------------------------------------------------------------
def ask(question):
    """Returns (answer, list of the searches it made)."""
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    searches = []
    # TODO 2 - the loop: ask the model; if it wants the tool, run the search and give it the results; repeat.
    # HINT:  for step in range(5):                                          # at most 5 rounds
    #            result = client.chat(messages, tools=[SEARCH_TOOL])
    #            if not result.wants_tools:                                 # no tool wanted: this is the final answer
    #                return result.text, searches
    #            messages.append(result.raw_message)                        # remember what the model asked
    #            for call in result.tool_calls:
    #                query = call.arguments["query"]
    #                searches.append(query)
    #                found = kb.search(query)                               # [(chunk id, text), ...]
    #                text = "\n".join("[%s] %s" % (chunk_id, chunk_text) for chunk_id, chunk_text in found)
    #                messages.append({"role": "tool", "tool_call_id": call.id, "content": text})
    return "TODO 2 is not done yet", searches


TESTS = [
    "Hi! What can you help me with?",
    "How long is the warranty on the Falcon S2 Pro?",
    "The display says E-4210. What should I do?",
    "Do you sell the Pixel 9 phone?",
    "Which battery lasts longer, the Orion X3 or the Falcon S1?",
    "Who won the football world cup?",
]
for question in TESTS:
    answer, searches = ask(question)
    print("Q:", question)
    print("   searches (%d): %s" % (len(searches), searches))
    print("   answer:", answer)
    print()


# ---- The chat app (ready for you: nothing to fill in here) -------------------------------------
import gradio as gr


def run_agent(question):
    if not question.strip():
        return "", ""
    answer, searches = ask(question)
    return answer, "\n".join("%d. %s" % (n, s) for n, s in enumerate(searches, 1)) or "(no search)"


with gr.Blocks(title="Search agent") as app:
    gr.Markdown("## Search agent\nAsk a question. The agent decides if it needs to search, and shows what it searched for.")
    box = gr.Textbox(label="Your question", placeholder="for example: Hi!   or   The display says E-4210")
    answer_box = gr.Textbox(label="Answer (with [sources])", lines=4)
    search_box = gr.Textbox(label="What the agent searched for", lines=3)
    box.submit(run_agent, box, [answer_box, search_box])
    gr.Button("Ask", variant="primary").click(run_agent, box, [answer_box, search_box])
    gr.Examples(TESTS, inputs=box, fn=run_agent, outputs=[answer_box, search_box], run_on_click=True)

app.launch(inbrowser=True)                        # opens in your browser: http://127.0.0.1:7860
