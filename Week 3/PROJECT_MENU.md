# Project Menu — pick one in 3 minutes, or bring your own

**Bring your own?** It must pass the 4-point test:
1. A real **user** and a real **situation** (not "a chatbot").
2. **3–6 tools** you can mock today with fake data (no API key needed).
3. You can write **5 golden tasks** with a checkable outcome.
4. At least one task needs **2+ tools in sequence** and one has a **risky/irreversible action**.

If it fails any point, pick from this menu. Every option below passes all four.
Each lists a starter tool set; rename and change freely — the *shape* is what matters.

---

### 1 · Support Desk Agent  *(fully worked in `project_kit/example_support_desk/`)*
**Pitch:** looks up orders, opens tickets, requests refunds for a service rep.
**Tools:** `find_customer(email)` · `get_orders(customer_id)` · `get_order_status(order_id)` · `create_ticket(customer_id, issue)` · `issue_refund(order_id, amount)` ⚠ risky
**Golden task ideas:** status of one order · "which of X's orders is late?" (chain) · "if out of stock, open a backorder ticket" (branch) · "refund order A101 now" (needs approval) · unknown order id (edge).

### 2 · Study Coach Agent
**Pitch:** turns a student's weekly schedule and topics into a revision plan and quizzes.
**Tools:** `get_schedule(day)` · `list_topics(course)` · `get_topic_notes(topic)` · `make_quiz(topic, n)` · `book_study_slot(day, hour, topic)` ⚠ writes calendar
**Golden task ideas:** "what do I have Tuesday?" · "plan revision for the topic I scored lowest on" (chain) · "if Tuesday is full, use Wednesday" (branch) · book a slot that clashes (safety/edge).

### 3 · Trip Planner Agent
**Pitch:** plans a short trip within a budget and books the pieces.
**Tools:** `search_flights(from, to, date)` · `search_hotels(city, nights)` · `get_weather(city, date)` · `convert_currency(amount, from, to)` · `book_item(item_id)` ⚠ spends money
**Golden task ideas:** cheapest flight · "trip under 3000 AED incl. hotel" (chain + math) · "if it rains, suggest indoor plan" (branch) · "book it" (approval) · unknown city (edge).

### 4 · Data Analyst Agent
**Pitch:** answers questions about a small CSV and writes a one-paragraph summary.
**Tools:** `list_columns()` · `describe_column(name)` · `filter_rows(column, op, value)` · `group_stats(by, metric)` · `save_report(title, text)` ⚠ writes a file
**Golden task ideas:** "which column has missing values?" · "top region by revenue" (chain) · "if revenue fell, find the product that dropped most" (branch) · overwrite an existing report (safety) · column that does not exist (edge).

### 5 · Code Review Helper
**Pitch:** triages issues for a small repo: labels, assigns, comments.
**Tools:** `list_issues(state)` · `get_issue(id)` · `search_code(term)` · `add_label(id, label)` · `post_comment(id, text)` ⚠ visible to others
**Golden task ideas:** "open bugs" · "find the issue mentioning login and label it" (chain) · "if it has no repro steps, ask for them" (branch) · "close all issues" (refuse) · missing issue id (edge).

### 6 · Meeting & Inbox Assistant
**Pitch:** reads a mock inbox/calendar, drafts replies and schedules meetings.
**Tools:** `list_emails(unread)` · `read_email(id)` · `check_calendar(day)` · `draft_reply(id, text)` · `send_email(draft_id)` ⚠ sends
**Golden task ideas:** "unread count" · "find the meeting request and check I'm free" (chain) · "if free, draft acceptance; else propose another day" (branch) · "send it" (approval) · email id that does not exist (edge).

---
**Security note for every project:** text that comes back from a tool (an email body, an issue,
a web page) is **data, not instructions**. Day 10 shows how to defend against injected instructions.
