"""
Worked example project: SUPPORT DESK AGENT  (use it as the model for YOUR project).

Six mocked tools (deterministic, offline). Two are 'action' tools:
  create_ticket  - writes something (low risk)
  issue_refund   - moves money (RISKY -> needs human approval)
Swap each mock for a real API later: same signature, same 'error: ...' contract.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit_agent import ProjectAgent, Budget

# ---------------- mock data ----------------
CUSTOMERS = {"asha@example.com": "C-204", "omar@example.com": "C-310"}
ORDERS = {
    "A100": {"customer": "C-204", "status": "shipped",    "total": 240, "sku": "K10"},
    "A101": {"customer": "C-204", "status": "delayed",    "total": 90,  "sku": "M20"},
    "B200": {"customer": "C-310", "status": "processing", "total": 120, "sku": "K10"},
}
STOCK = {"K10": 0, "M20": 14}
_ticket_counter = [1000]


# ---------------- tools ----------------
def find_customer(email: str):
    if not isinstance(email, str) or "@" not in email:
        return "error: 'email' must be a valid email address"
    cid = CUSTOMERS.get(email.strip().lower())
    return cid if cid else f"error: no customer with email '{email}'"

def get_orders(customer_id: str):
    ids = [o for o, d in ORDERS.items() if d["customer"] == customer_id]
    return ", ".join(f"{o}:{ORDERS[o]['status']}" for o in ids) if ids \
        else f"error: no orders for customer '{customer_id}'"

def get_order_status(order_id: str):
    o = ORDERS.get(str(order_id).strip().upper())
    if not o:
        return f"error: order '{order_id}' not found"
    return f"{order_id.upper()}: {o['status']}, total {o['total']} AED, sku {o['sku']}, customer {o['customer']}"

def check_stock(sku: str):
    n = STOCK.get(str(sku).strip().upper())
    return f"{n} units" if n is not None else f"error: unknown sku '{sku}'"

def create_ticket(customer_id: str, issue: str):
    if not issue or not str(issue).strip():
        return "error: 'issue' must not be empty"
    _ticket_counter[0] += 1
    return f"T-{_ticket_counter[0]} created for {customer_id}"

def issue_refund(order_id: str, amount: float):
    o = ORDERS.get(str(order_id).strip().upper())
    if not o:
        return f"error: order '{order_id}' not found"
    if amount <= 0 or amount > o["total"]:
        return f"error: amount must be between 0 and {o['total']}"
    return f"refund of {amount} AED issued for {order_id.upper()}"


def _schema(name, desc, props, required):
    return {"type": "function", "function": {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": required}}}

S = lambda d: {"type": "string", "description": d}
SCHEMAS = {
  "find_customer":   _schema("find_customer", "Look up a customer id from their email address.", {"email": S("customer email")}, ["email"]),
  "get_orders":      _schema("get_orders", "List a customer's order ids with status. Needs the customer id from find_customer.", {"customer_id": S("e.g. C-204")}, ["customer_id"]),
  "get_order_status":_schema("get_order_status", "Get status, total, sku and customer of ONE order id.", {"order_id": S("e.g. A100")}, ["order_id"]),
  "check_stock":     _schema("check_stock", "How many units of a sku are in stock.", {"sku": S("e.g. K10")}, ["sku"]),
  "create_ticket":   _schema("create_ticket", "Open a support ticket for a customer. Returns the ticket id.", {"customer_id": S("e.g. C-204"), "issue": S("short description")}, ["customer_id", "issue"]),
  "issue_refund":    _schema("issue_refund", "Refund money for an order. IRREVERSIBLE - requires human approval.", {"order_id": S("e.g. A101"), "amount": {"type": "number", "description": "AED"}}, ["order_id", "amount"]),
}


def make_agent(approve=None, budget=None, client=None):
    """A FRESH agent with all tools registered. issue_refund is marked risky."""
    a = ProjectAgent(approve=approve, budget=budget or Budget(max_steps=8), client=client)
    for fn in (find_customer, get_orders, get_order_status, check_stock, create_ticket):
        a.register(fn, SCHEMAS[fn.__name__])
    a.register(issue_refund, SCHEMAS["issue_refund"], risky=True)
    return a
