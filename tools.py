"""
NimbusPay TriageBot Tools
Three required tools: FAQ lookup, account lookup, refund calculator
Bonus: open a support ticket
"""

import difflib
from data import FAQ, ACCOUNTS, REFUND_CAP

# Session memory (bonus: remembers last account looked up)
_session = {"last_account": None}


def faq_lookup(question: str) -> str:
    """Search the FAQ for an answer to the customer's question."""
    question_lower = question.lower()
    best_match = None
    best_score = 0.0

    for item in FAQ:
        # Check keyword overlap
        score = difflib.SequenceMatcher(None, question_lower, item["q"].lower()).ratio()
        # Also check keyword hits
        keywords = [w for w in question_lower.split() if len(w) > 3]
        keyword_hits = sum(1 for kw in keywords if kw in item["q"].lower() or kw in item["a"].lower())
        combined = score + (keyword_hits * 0.2)
        if combined > best_score:
            best_score = combined
            best_match = item

    if best_match and best_score > 0.3:
        return f"FAQ Answer: {best_match['a']}"
    return "NO_FAQ_MATCH"


def account_lookup(account_id: str) -> str:
    """Look up an account by ID and return balance and last transaction."""
    account_id = account_id.strip()
    if account_id in ACCOUNTS:
        acc = ACCOUNTS[account_id]
        _session["last_account"] = account_id
        return (
            f"Account {account_id} — {acc['name']}\n"
            f"Balance: ${acc['balance']:.2f}\n"
            f"Last transaction: {acc['last_transaction']}"
        )
    return f"Account {account_id} not found in the system."


def refund_calculator(amount_str: str) -> str:
    """Check if a refund amount is auto-eligible or requires escalation."""
    try:
        amount = float(amount_str.replace("$", "").strip())
    except ValueError:
        return "Invalid amount provided."

    if amount <= REFUND_CAP:
        return f"Refund of ${amount:.2f} is AUTO-APPROVED. Processing now."
    else:
        return f"ESCALATE: Refund of ${amount:.2f} exceeds the ${REFUND_CAP:.0f} auto-approval cap. Must be reviewed by a human agent."


def open_ticket(issue: str) -> str:
    """(Bonus) Open a support ticket for complex issues."""
    import random
    ticket_id = random.randint(10000, 99999)
    return f"Support ticket #{ticket_id} opened: '{issue}'. A human agent will respond within 24 hours."


def get_last_account() -> str:
    """(Bonus) Return the last account looked up this session."""
    if _session["last_account"]:
        return account_lookup(_session["last_account"])
    return "No account has been looked up in this session yet."
