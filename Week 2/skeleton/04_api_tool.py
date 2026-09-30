"""
04 · Connect a tool to a REAL API — with error handling & validation.  (NEW)

So far our tools returned data from a dict. Real tools call the outside world,
where things go wrong: bad arguments, timeouts, non-200 status codes, malformed
JSON, and missing fields. A production tool NEVER crashes the agent — it returns
a clear "error: ..." string the model can read and react to.

The tool here uses the free, no-key Open-Meteo API (geocode a city -> current
temperature). You'll add the two validations that matter:
  1. INPUT validation  — check the arguments the MODEL gave us before we act.
  2. OUTPUT validation  — check the API's RESPONSE before we trust it.

-------------------------------------------------------------------
YOUR TASKS  (all inside get_current_temperature)
  TODO 1 · INPUT: if `city` isn't a non-empty string, return an "error: ..." string.
  TODO 2 · wrap the network calls in try/except and handle, at least:
           requests.exceptions.Timeout, requests.exceptions.RequestException,
           and (ValueError, KeyError, TypeError). Return "error: ..." each time.
  TODO 3 · OUTPUT: after geocoding, if there are no results, return a clear error;
           after the weather call, if temperature is missing, return an error.
-------------------------------------------------------------------
Run it (needs internet):  python skeleton/04_api_tool.py
Stuck?   trainer/04_api_tool.py has the full version.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import requests
from utils.llm_client import LLMClient

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WX_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 8


def get_current_temperature(city: str):
    """Return the current temperature for a city, or an 'error: ...' string."""
    # TODO 1: INPUT validation — reject a missing/blank city with an error string.

    # TODO 2: wrap the calls below in try/except (see docstring for what to catch).
    geo = requests.get(GEO_URL, params={"name": city, "count": 1}, timeout=TIMEOUT)
    geo.raise_for_status()
    geo_data = geo.json()

    # TODO 3: OUTPUT validation — handle 'no results' before indexing.
    results = geo_data.get("results")
    lat = results[0]["latitude"]
    lon = results[0]["longitude"]
    name = results[0].get("name", city)

    wx = requests.get(WX_URL, params={"latitude": lat, "longitude": lon,
                                      "current": "temperature_2m"}, timeout=TIMEOUT)
    wx.raise_for_status()
    current = wx.json().get("current")
    # TODO 3 (cont.): handle a response with no temperature before using it.
    return f"{name}: {current['temperature_2m']}°C"


TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_current_temperature",
        "description": "Get the current temperature (Celsius) for a city name.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Dubai'."},
            },
            "required": ["city"],
        },
    },
}]


def run(goal):
    client = LLMClient()
    messages = [{"role": "user", "content": goal}]
    for step in range(1, 5):
        result = client.chat(messages, tools=TOOLS)
        if not result.wants_tools:
            return result.text
        messages.append(result.raw_message)
        for call in result.tool_calls:
            out = get_current_temperature(**call.arguments)
            print(f"[step {step}] {call.name}({call.arguments}) -> {out}")
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": str(out)})
    return "Stopped: step limit."


if __name__ == "__main__":
    # Once your TODOs are done, these should print clean 'error:' lines, not crash:
    print("empty city ->", get_current_temperature(""))
    print("nonsense  ->", get_current_temperature("zzzxqwmadeupcity"))
    print("real city ->", get_current_temperature("Dubai"))
    print()
    print("FINAL:", run("Is it hotter in Dubai or London right now?"))
