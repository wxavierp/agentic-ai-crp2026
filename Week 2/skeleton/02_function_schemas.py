"""
02 · Function schemas & structured outputs.  (NEW · builds on 01)

The schema IS the contract. A good schema makes the model reliable:
  - a clear `description` tells it WHEN to use the tool,
  - typed `properties` (string / number / boolean / enum) constrain the values,
  - `required` says which arguments must be present.

Here the agent has TWO tools. get_price is written for you. You will write the
schema for the SECOND tool (with an `enum`), and finish the dispatch table so
the loop can run whichever tool the model chose.

-------------------------------------------------------------------
YOUR TASKS
  TODO 1 · write the schema for convert_currency: a required number `amount`
           and a required string `to_currency` restricted to an enum
           ["USD", "AED", "INR"].
  TODO 2 · finish DISPATCH so "convert_currency" routes to convert_currency.
  TODO 3 · in run_tool(), call the right function with call.arguments and
           return a friendly "error: ..." string instead of crashing.
-------------------------------------------------------------------
Run it:  python skeleton/02_function_schemas.py
Stuck?   trainer/02_function_schemas.py has the full version.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.llm_client import LLMClient

CATALOGUE = {"widget": 25, "gadget": 40, "sprocket": 12}

def get_price(item: str, currency: str = "USD"):
    base = CATALOGUE.get(item.strip().lower())
    if base is None:
        return f"error: no price for '{item}'"
    rate = {"USD": 1.0, "AED": 3.67, "INR": 83.0}.get(currency, 1.0)
    return f"{round(base * rate, 2)} {currency}"

def convert_currency(amount: float, to_currency: str):
    rate = {"USD": 1.0, "AED": 3.67, "INR": 83.0}.get(to_currency, 1.0)
    return round(amount * rate, 2)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "Look up the catalogue price of a single item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {"type": "string",
                             "description": "Item name, e.g. 'widget'."},
                    "currency": {"type": "string",
                                 "enum": ["USD", "AED", "INR"],
                                 "description": "Currency for the price."},
                },
                "required": ["item"],
            },
        },
    },
    # TODO 1: add the convert_currency schema here (see the docstring).
]

# TODO 2: add "convert_currency": convert_currency
DISPATCH = {"get_price": get_price}


def run_tool(call):
    fn = DISPATCH.get(call.name)
    if fn is None:
        return f"error: unknown tool '{call.name}'"
    # TODO 3: call fn(**call.arguments); on a TypeError return a friendly error.
    return "error: run_tool not implemented yet"


def main():
    client = LLMClient()
    messages = [{"role": "user", "content": "How much is a gadget, in AED?"}]

    result = client.chat(messages, tools=TOOLS)
    if not result.wants_tools:
        print("No tool chosen:", result.text)
        return

    messages.append(result.raw_message)
    for call in result.tool_calls:
        out = run_tool(call)
        print(f"{call.name}({call.arguments}) -> {out}")
        messages.append({"role": "tool", "tool_call_id": call.id,
                         "content": str(out)})

    final = client.chat(messages, tools=TOOLS)
    print("\nFINAL:", final.text)


if __name__ == "__main__":
    main()
