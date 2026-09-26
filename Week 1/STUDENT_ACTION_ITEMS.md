# Week 1 — Student Action Items

Tick these off as you go. Week 1 is light on coding — most of the work is
setup, exploration, and one small build.

## Before Wednesday (Day 2)
- [ ] Install **Python 3.11+** and **VS Code** (+ Python extension)
- [ ] Install **Git** and create a **GitHub** account
- [ ] Create accounts: **ChatGPT**, **Claude**, **Gemini**
- [ ] Get **one API key** (OpenAI, or free Groq / Gemini)
- [ ] Clone/download this repo and open the `Week 1` folder

## During / after Wednesday (Day 2)
- [ ] Create a virtual env and `pip install -r requirements.txt`
- [ ] Copy `.env.example` → `.env` and add your key + `LLM_PROVIDER`
- [ ] Run `python skeleton/00_setup_check.py` — get a green success line
- [ ] Complete the 2 TODOs in `01_assistant_vs_agent.py` and run it
- [ ] Run `02_llm_reasoning_limits.py`; complete its 1 TODO
- [ ] **Explore:** give ChatGPT, Claude and Gemini the *same* task — note where they differ, and try to make one *act* (it can't — why?)
- [ ] Draft (on paper) a blueprint for an agent: its goal, tools, memory, actions

## Saturday lab (Day 3)
- [ ] **Lab 1:** finish `01_assistant_vs_agent.py`, push it
- [ ] **Lab 2 (deliverable):** complete `my_agent` in `03_agent_anatomy.py`
- [ ] **Lab 3 (coding):** complete the 4 TODOs in `04_agent_loop.py` so it solves `(23 * 7) + 19`
- [ ] *Stretch:* add a second tool to your loop
- [ ] *Extension:* add reflection in `05_reflection_loop.py` (self-check → retry)
- [ ] *Extension:* build the two-tool agent in `06_multi_tool_agent.py` (safe calculator)
- [ ] *Advanced:* try native function calling in `07_advanced_agent.py`

## Submit before Monday (Day 4 / Week 2)
- [ ] `03_agent_anatomy.py` with your blueprint filled in
- [ ] `04_agent_loop.py` completing the goal cleanly
- [ ] Everything pushed to your GitHub repo

## Reflect (optional, 5 min)
- What surprised you about where the LLM failed?
- Which of the four agent parts is hardest to get right, and why?
