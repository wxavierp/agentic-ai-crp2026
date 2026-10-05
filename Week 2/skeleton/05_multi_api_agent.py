"""
05 · A multi-tool agent over real APIs.  (NEW · Day 3 / Session 6)

Day 2 gave us the ToolAgent (03) and one robust API tool (04). Real agents have
SEVERAL tools and pick the right one per step. Here you add a SECOND free, no-key
Open-Meteo tool — elevation — beside temperature, then ask a question that needs
both.

-------------------------------------------------------------------
YOUR TASKS
  TODO 1 · finish get_elevation(): call the elevation API and validate the output
           (return a clean 'error: ...' string on any problem — never raise).
  TODO 2 · register BOTH tools on the agent in __main__.
-------------------------------------------------------------------
Needs internet (free, no key).
Run it:  python skeleton/05_multi_api_agent.py
Stuck?   trainer/05_multi_api_agent.py has the full version.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import requests
from utils.llm_client import LLMClient

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WX_URL = "https://api.open-meteo.com/v1/forecast"
ELEV_URL = "https://api.open-meteo.com/v1/elevation"
TIMEOUT = 8
MAX_STEPS = 6


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


def _geocode(city):
    """Given a city, return ((lat, lon, name), None) or (None, 'error: ...'). (given)"""
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
    """Current temperature for a city, or 'error: ...'. (given — from Day 2's 04)"""
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


def get_elevation(city: str):
    """Elevation in metres for a city, or 'error: ...'."""
    geo, err = _geocode(city)
    if err:
        return err
    lat, lon, name = geo
    # TODO 1: call ELEV_URL with latitude/longitude + a timeout; raise_for_status;
    #         read 'elevation' (a list) from the JSON; validate it's present;
    #         return f"{name}: {elev[0]} m above sea level". Catch Timeout,
    #         RequestException, and (ValueError, KeyError, TypeError, IndexError),
    #         returning a clean 'error: ...' string for each.
    return "error: get_elevation not implemented yet"


TEMP_SCHEMA = {"type": "function", "function": {
    "name": "get_current_temperature",
    "description": "Get the current temperature (Celsius) for a city name.",
    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}
ELEV_SCHEMA = {"type": "function", "function": {
    "name": "get_elevation",
    "description": "Get the elevation (metres above sea level) for a city name.",
    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}


if __name__ == "__main__":
    agent = ToolAgent(system="You are a helpful assistant. Use the tools when needed; "
                             "take one step at a time.")
    # TODO 2: register BOTH get_current_temperature and get_elevation with their schemas.

    answer = agent.run("Is Dubai hotter than London right now, and which city sits higher?")
    print("\nFINAL:", answer)
