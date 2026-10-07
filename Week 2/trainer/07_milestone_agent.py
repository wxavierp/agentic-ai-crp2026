"""
07 · MODULE 2 MILESTONE — the multi-tool agent.  (TRAINER)  [Day 4 / Session 7]

The Module-2 deliverable: EVERYTHING from the week in ONE agent — not a single
tool, but the whole toolbox, with the model choosing among them.

  - the reusable ToolAgent (03) with MAX_STEPS,
  - TWO hardened real-API tools (04 + 05): temperature AND elevation,
  - the automation bridge (06): a webhook tool that triggers a workflow,
  - a clean contract: every tool returns a value or an 'error: ...' string.

So the milestone goes beyond 04 (one API tool): it shows an agent PICKING the
right tool across several, chaining them, AND firing an automation — then it
proves every tool fails cleanly.

Run it (needs internet for the APIs; the webhook uses a mock):
    python trainer/07_milestone_agent.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import requests
from utils.llm_client import LLMClient

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WX_URL = "https://api.open-meteo.com/v1/forecast"
ELEV_URL = "https://api.open-meteo.com/v1/elevation"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")   # unset -> the mock below
TIMEOUT = 8
MAX_STEPS = 8


class ToolAgent:
    """The reusable agent from 03 — register tools, loop until the model answers."""
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


# ---- shared geocoding helper (input + output validated) ----
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


# ---- tool 1: a real API (from 04) ----
def get_current_temperature(city: str):
    geo, err = _geocode(city)
    if err:
        return err
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


# ---- tool 2: a second real API (from 05) ----
def get_elevation(city: str):
    geo, err = _geocode(city)
    if err:
        return err
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


# ---- tool 3: the automation bridge (from 06) ----
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
    """Assemble the module: one agent, three tools (two APIs + an automation)."""
    agent = ToolAgent(system="You are a helpful assistant with tools for weather, elevation "
                             "and triggering automations. Use the right tool(s), one step at "
                             "a time, then answer.")
    agent.register(get_current_temperature, TEMP_SCHEMA)
    agent.register(get_elevation, ELEV_SCHEMA)
    agent.register(trigger_workflow, TRIGGER_SCHEMA)
    return agent


def failure_suite():
    """Prove every tool fails cleanly — the first checks need no model and no network."""
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

    # 1) multi-tool reasoning: needs the weather AND elevation tools
    print("Q1:", agent.run("Is Dubai hotter than London right now, and which city sits higher?"))
    print()
    # 2) reasoning + automation: check the weather, then fire a workflow
    print("Q2:", agent.run("If Dubai is hotter than London right now, email the team to say so."))
    # Milestone: the agent picks across THREE tools, chains them, AND fails cleanly everywhere.
