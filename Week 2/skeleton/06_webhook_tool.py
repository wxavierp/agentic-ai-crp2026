"""
06 · A webhook tool — the bridge to workflow automation (n8n).  (NEW · Day 3 / Session 6)

An agent reasons about open-ended goals; a workflow (n8n) runs fixed steps when a
trigger fires. Bridge them: give the agent a tool that POSTs to a webhook. The
AGENT decides WHEN; the WORKFLOW does the reliable work.

-------------------------------------------------------------------
YOUR TASKS  (inside trigger_workflow)
  TODO 1 · input validation: 'event' must be a non-empty string; 'payload' must be
           a dict (default to {}). Return a clean 'error: ...' otherwise.
  TODO 2 · if WEBHOOK_URL is unset, call _mock_webhook and return its result;
           otherwise POST {"event":..., "payload":...} to WEBHOOK_URL with a
           timeout, raise_for_status, and handle Timeout / RequestException.
-------------------------------------------------------------------
Runs with NO network and NO live n8n (uses the mock) when WEBHOOK_URL is unset.
Run it:  python skeleton/06_webhook_tool.py
Stuck?   trainer/06_webhook_tool.py has the full version.
"""

import sys, os, json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import requests
from utils.llm_client import LLMClient

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TIMEOUT = 8
MAX_STEPS = 6


def _mock_webhook(event, payload):
    """Stands in for n8n when no WEBHOOK_URL is configured. (given)"""
    print(f"   [mock n8n] trigger received: event={event!r} payload={payload!r}")
    return {"status": "accepted", "event": event, "ran": ["log", "notify"]}


def trigger_workflow(event: str, payload: dict | None = None):
    """Fire an automation workflow. Never crash — return a clean 'error: ...' on failure."""
    # TODO 1: validate 'event' (non-empty str) and 'payload' (dict; default {}).

    # TODO 2: if no WEBHOOK_URL -> return _mock_webhook(...); else POST to it with a
    #         timeout and clean error handling.
    return "error: trigger_workflow not implemented yet"


TRIGGER_SCHEMA = {"type": "function", "function": {
    "name": "trigger_workflow",
    "description": ("Fire an automation workflow (e.g. send a summary email, log a record). "
                    "Use when the user asks to DO something repeatable, not just answer."),
    "parameters": {"type": "object", "properties": {
        "event": {"type": "string", "description": "The workflow to run, e.g. 'email_summary'."},
        "payload": {"type": "object", "description": "Data for the workflow."}},
        "required": ["event"]}}}


class ToolAgent:
    def __init__(self, system=None):
        self.client = LLMClient(); self.schemas = []; self.functions = {}; self.system = system
    def register(self, fn, schema):
        self.functions[schema["function"]["name"]] = fn; self.schemas.append(schema)
    def _run_tool(self, call):
        fn = self.functions.get(call.name)
        if fn is None: return f"error: unknown tool '{call.name}'"
        try: return fn(**call.arguments)
        except Exception as e: return f"error: {call.name} failed: {e}"
    def run(self, goal):
        messages = ([{"role": "system", "content": self.system}] if self.system else []) + \
                   [{"role": "user", "content": goal}]
        for step in range(1, MAX_STEPS + 1):
            result = self.client.chat(messages, tools=self.schemas)
            if not result.wants_tools:
                return result.text
            messages.append(result.raw_message)
            for call in result.tool_calls:
                out = self._run_tool(call)
                print(f"[step {step}] {call.name}({call.arguments}) -> {out}")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": str(out)})
        return "Stopped: reached the tool-step limit."


if __name__ == "__main__":
    print("blank event ->", trigger_workflow(""))
    print("ok event    ->", trigger_workflow("email_summary", {"to": "team@example.com",
                                                               "text": "Build is green."}))
    print()
    agent = ToolAgent(system="You can trigger automation workflows with trigger_workflow. "
                             "Use it when the user asks you to DO a repeatable action.")
    agent.register(trigger_workflow, TRIGGER_SCHEMA)
    print("\nFINAL:", agent.run("Please email the team a note that tonight's build passed."))
