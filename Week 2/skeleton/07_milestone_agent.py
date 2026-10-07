"""
07 · MODULE 2 MILESTONE — the multi-tool agent.  (NEW · Day 4 / Session 7)

Assemble the WHOLE module into one agent — not a single tool, the whole toolbox:
  - the reusable ToolAgent (03) with MAX_STEPS,
  - TWO hardened real-API tools (04 + 05): temperature AND elevation,
  - the automation bridge (06): a webhook tool,
  - every tool returns a value or a clean 'error: ...' string — never crashes.

This goes beyond 04: the agent PICKS the right tool across several, chains them,
and can fire an automation. The tools below are the ones you built on Days 1–3 —
your job is the assembly and the loop.

-------------------------------------------------------------------
YOUR TASKS
  TODO 1 · (ToolAgent.run) finish the loop: ask the model; if it wants no tool,
           return the answer; else append the assistant message and run each tool
           call, appending a 'tool' message with the matching tool_call_id.
  TODO 2 · (build_agent) register ALL THREE tools with their schemas.
-------------------------------------------------------------------
Needs internet for the APIs; the webhook uses a mock. Run it:
    python skeleton/07_milestone_agent.py
Stuck?   trainer/07_milestone_agent.py has the full version.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import requests
from utils.llm_client import LLMClient

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WX_URL = "https://api.open-meteo.com/v1/forecast"
ELEV_URL = "https://api.open-meteo.com/v1/elevation"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TIMEOUT = 8
MAX_STEPS = 8


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
            # TODO 1: result = self.client.chat(...); if not result.wants_tools: return it;
            #         else append result.raw_message and run each tool call, appending a
            #         {"role":"tool","tool_call_id":...,"content":...} message.
            pass
        return "Stopped: reached the tool-step limit."


# ---- the tools you built on Days 1–3 (given) ----
def _geocode(city):
    if not isinstance(city, str) or not city.strip():
        return None, "error: 'city' must be a non-empty string"
    try:
        r = requests.get(GEO_URL, params={"name": city, "count": 1}, timeout=TIMEOUT)
        r.raise_for_status()
        results = r.json().get("results")
        if not results:
            return None, f"error: could not find a city named '{city}'"
        g = results[0]
        return (g["latitude"], g["longitude"], g.get("name", city)), None
    except requests.exceptions.Timeout:
        return None, "error: geocoding timed out"
    except requests.exceptions.RequestException as e:
        return None, f"error: network/API problem: {e}"
    except (ValueError, KeyError, TypeError) as e:
        return None, f"error: unexpected geocoding response: {e}"

def get_current_temperature(city: str):
    geo, err = _geocode(city)
    if err: return err
    lat, lon, name = geo
    try:
        r = requests.get(WX_URL, params={"latitude": lat, "longitude": lon,
                                          "current": "temperature_2m"}, timeout=TIMEOUT)
        r.raise_for_status()
        current = r.json().get("current")
        if not current or "temperature_2m" not in current:
            return "error: weather response missing temperature"
        return f"{name}: {current['temperature_2m']}°C"
    except requests.exceptions.Timeout:
        return "error: weather API timed out"
    except requests.exceptions.RequestException as e:
        return f"error: network/API problem: {e}"
    except (ValueError, KeyError, TypeError) as e:
        return f"error: unexpected weather response: {e}"

def get_elevation(city: str):
    geo, err = _geocode(city)
    if err: return err
    lat, lon, name = geo
    try:
        r = requests.get(ELEV_URL, params={"latitude": lat, "longitude": lon}, timeout=TIMEOUT)
        r.raise_for_status()
        elev = r.json().get("elevation")
        if not elev:
            return "error: elevation response missing data"
        return f"{name}: {elev[0]} m above sea level"
    except requests.exceptions.Timeout:
        return "error: elevation API timed out"
    except requests.exceptions.RequestException as e:
        return f"error: network/API problem: {e}"
    except (ValueError, KeyError, TypeError, IndexError) as e:
        return f"error: unexpected elevation response: {e}"

def trigger_workflow(event: str, payload: dict | None = None):
    if not isinstance(event, str) or not event.strip():
        return "error: 'event' must be a non-empty string"
    payload = payload or {}
    if not isinstance(payload, dict):
        return "error: 'payload' must be an object"
    if not WEBHOOK_URL:
        print(f"   [mock n8n] trigger received: event={event!r} payload={payload!r}")
        return f"workflow triggered (mock): {event}"
    try:
        r = requests.post(WEBHOOK_URL, json={"event": event, "payload": payload}, timeout=TIMEOUT)
        r.raise_for_status()
        return f"workflow triggered: {event} (status {r.status_code})"
    except requests.exceptions.Timeout:
        return "error: webhook timed out"
    except requests.exceptions.RequestException as e:
        return f"error: could not reach the workflow: {e}"


CITY_PARAM = {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
TEMP_SCHEMA = {"type": "function", "function": {
    "name": "get_current_temperature",
    "description": "Get the current temperature (Celsius) for a city name.", "parameters": CITY_PARAM}}
ELEV_SCHEMA = {"type": "function", "function": {
    "name": "get_elevation",
    "description": "Get the elevation (metres above sea level) for a city name.", "parameters": CITY_PARAM}}
TRIGGER_SCHEMA = {"type": "function", "function": {
    "name": "trigger_workflow",
    "description": ("Fire an automation workflow (e.g. email a summary). Use when the user "
                    "asks you to DO a repeatable action, not just answer a question."),
    "parameters": {"type": "object", "properties": {
        "event": {"type": "string", "description": "The workflow, e.g. 'email_summary'."},
        "payload": {"type": "object", "description": "Data for the workflow."}},
        "required": ["event"]}}}


def build_agent():
    agent = ToolAgent(system="You are a helpful assistant with tools for weather, elevation "
                             "and triggering automations. Use the right tool(s), one step at "
                             "a time, then answer.")
    # TODO 2: register get_current_temperature, get_elevation AND trigger_workflow.
    return agent


def failure_suite():
    print("--- failure suite (no tool may crash) ---")
    print("temp blank city   ->", get_current_temperature(""))
    print("temp non-string   ->", get_current_temperature(None))
    print("temp nonsense     ->", get_current_temperature("zzzxqwmadeupcity"))
    print("elev nonsense     ->", get_elevation("zzzxqwmadeupcity"))
    print("workflow blank    ->", trigger_workflow(""))
    print("--- end suite ---\n")


if __name__ == "__main__":
    failure_suite()
    agent = build_agent()
    print("Q1:", agent.run("Is Dubai hotter than London right now, and which city sits higher?"))
    print()
    print("Q2:", agent.run("If Dubai is hotter than London right now, email the team to say so."))
