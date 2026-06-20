"""
TriageBot — LangGraph + LangChain support agent for NimbusPay
 
Graph structure:
  [START] → classify → faq_node / tool_node / escalate_node
                             ↓
                          review_node ←──────────┐
                             ↓                    │
                     (pass) respond            (fail, retry < 3)
                             ↓
                           [END]
"""

import os
import re
from typing import TypedDict, Literal, Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from tools import faq_lookup, account_lookup, refund_calculator, open_ticket, get_last_account

# ── LLM ────────────────────────────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.2,
)

# ── State ───────────────────────────────────────────────────────────────────────
class BotState(TypedDict):
    message: str                        # customer's input
    route: Optional[str]                # faq | tool | escalate
    tool_result: Optional[str]          # output from whichever tool ran
    draft: Optional[str]                # TriageBot's draft reply
    review_result: Optional[str]        # pass | fail
    review_reason: Optional[str]        # why it failed
    final_reply: Optional[str]          # what gets shown to the user
    retry_count: int                    # loop guard
    path_log: list                      # breadcrumb trail for the demo


# ── Helper: call LLM ────────────────────────────────────────────────────────────
def call_llm(system: str, human: str) -> str:
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{input}")])
    chain = prompt | llm
    return chain.invoke({"input": human}).content.strip()


# ── Node 1: classify ────────────────────────────────────────────────────────────
def classify(state: BotState) -> BotState:
    msg = state["message"]
    system = """You are a router for a fintech support agent.
Given a customer message, reply with exactly one word:
- faq      → general question answerable from documentation
- tool     → needs account lookup or refund calculation (mentions account number, balance, refund amount)
- escalate → complaint, anger, legal threat, or request to speak to a human

Reply with only: faq, tool, or escalate"""

    route = call_llm(system, msg).lower().strip()
    if route not in ("faq", "tool", "escalate"):
        route = "faq"  # safe default

    state["route"] = route
    state["path_log"].append(f"classify → {route}")
    return state


# ── Node 2a: faq_node ───────────────────────────────────────────────────────────
def faq_node(state: BotState) -> BotState:
    result = faq_lookup(state["message"])
    if result == "NO_FAQ_MATCH":
        result = "I couldn't find a specific answer in our FAQ. Let me connect you with a support agent."
    state["tool_result"] = result
    state["path_log"].append("faq_node → FAQ lookup")
    return state


# ── Node 2b: tool_node ──────────────────────────────────────────────────────────
def tool_node(state: BotState) -> BotState:
    msg = state["message"]
    log = []

    # Extract account ID
    acct_match = re.search(r'\b(\d{4})\b', msg)
    # Extract dollar amount
    amt_match = re.search(r'\$\s*(\d+(?:\.\d+)?)', msg)

    results = []

    if acct_match:
        acct_id = acct_match.group(1)
        res = account_lookup(acct_id)
        results.append(res)
        log.append(f"account_lookup({acct_id})")

    if amt_match and ("refund" in msg.lower() or "reimburse" in msg.lower() or "charge" in msg.lower()):
        amount = amt_match.group(1)
        res = refund_calculator(amount)
        results.append(res)
        log.append(f"refund_calculator({amount})")

    if not results:
        # fallback: try FAQ
        results.append(faq_lookup(msg))
        log.append("faq_lookup (fallback)")

    state["tool_result"] = "\n".join(results)
    state["path_log"].append("tool_node → " + ", ".join(log))
    return state


# ── Node 2c: escalate_node ──────────────────────────────────────────────────────
def escalate_node(state: BotState) -> BotState:
    ticket = open_ticket(state["message"])
    state["tool_result"] = f"ESCALATING TO HUMAN AGENT. {ticket}"
    state["path_log"].append("escalate_node → human escalation")
    return state


# ── Node 3: draft_node ──────────────────────────────────────────────────────────
def draft_node(state: BotState) -> BotState:
    system = """You are TriageBot, a professional support assistant for NimbusPay.
Write a clear, concise, friendly reply to the customer.
Use the tool result as your source of truth.
If the result says ESCALATE, tell the customer you're escalating — do NOT process the request yourself.
Keep it under 3 sentences."""

    human = f"Customer message: {state['message']}\nTool result: {state['tool_result']}"
    draft = call_llm(system, human)
    state["draft"] = draft
    state["path_log"].append(f"draft_node → draft written (retry #{state['retry_count']})")
    return state


# ── Node 4: review_node ─────────────────────────────────────────────────────────
REVIEW_RULES = """You are a quality reviewer for a fintech support bot. Check the draft reply against these rules:
1. Must NOT promise a refund if the amount exceeds $50 (that requires human approval).
2. Must NOT share account details if no account was looked up.
3. Must NOT ignore an escalation — if the tool result says ESCALATE, the reply must mention escalation.
4. Must be polite and professional (no rudeness, no ALL CAPS shouting).
5. Must be relevant to the customer's question.

Reply with exactly:
PASS — if all rules are satisfied
FAIL: <reason> — if any rule is broken"""

def review_node(state: BotState) -> BotState:
    human = (
        f"Customer message: {state['message']}\n"
        f"Tool result: {state['tool_result']}\n"
        f"Draft reply: {state['draft']}"
    )
    verdict = call_llm(REVIEW_RULES, human)

    if verdict.upper().startswith("PASS"):
        state["review_result"] = "pass"
        state["review_reason"] = None
        state["path_log"].append("review_node → PASS")
    else:
        state["review_result"] = "fail"
        state["review_reason"] = verdict
        state["path_log"].append(f"review_node → FAIL ({verdict[:60]}...)")

    return state


# ── Node 5: respond ─────────────────────────────────────────────────────────────
def respond(state: BotState) -> BotState:
    state["final_reply"] = state["draft"]
    state["path_log"].append("respond → reply sent to customer")
    return state


# ── Node 6: redo ────────────────────────────────────────────────────────────────
def redo_node(state: BotState) -> BotState:
    """Rewrite the draft, taking the review feedback into account."""
    system = f"""You are TriageBot rewriting a failed draft.
The previous draft broke a rule: {state['review_reason']}
Fix it. Use the tool result. Keep under 3 sentences. Be professional."""
    human = f"Customer message: {state['message']}\nTool result: {state['tool_result']}"
    state["draft"] = call_llm(system, human)
    state["retry_count"] = state["retry_count"] + 1
    state["path_log"].append(f"redo_node → rewriting (retry #{state['retry_count']})")
    return state


# ── Routing functions ────────────────────────────────────────────────────────────
def route_after_classify(state: BotState) -> Literal["faq_node", "tool_node", "escalate_node"]:
    return state["route"] + "_node"  # type: ignore

def route_after_review(state: BotState) -> Literal["respond", "redo_node"]:
    if state["review_result"] == "pass":
        return "respond"
    if state["retry_count"] >= 3:
        # Cap the loop — force through after 3 retries
        state["path_log"].append("review_node → max retries reached, forcing through")
        return "respond"
    return "redo_node"


# ── Build the graph ──────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(BotState)

    g.add_node("classify",      classify)
    g.add_node("faq_node",      faq_node)
    g.add_node("tool_node",     tool_node)
    g.add_node("escalate_node", escalate_node)
    g.add_node("draft_node",    draft_node)
    g.add_node("review_node",   review_node)
    g.add_node("redo_node",     redo_node)
    g.add_node("respond",       respond)

    g.set_entry_point("classify")

    g.add_conditional_edges("classify", route_after_classify, {
        "faq_node":      "faq_node",
        "tool_node":     "tool_node",
        "escalate_node": "escalate_node",
    })

    # All three paths converge on draft_node
    g.add_edge("faq_node",      "draft_node")
    g.add_edge("tool_node",     "draft_node")
    g.add_edge("escalate_node", "draft_node")

    g.add_edge("draft_node", "review_node")

    g.add_conditional_edges("review_node", route_after_review, {
        "respond":  "respond",
        "redo_node": "redo_node",
    })

    g.add_edge("redo_node", "review_node")  # loop back
    g.add_edge("respond",   END)

    return g.compile()


graph = build_graph()


def run(message: str) -> dict:
    """Run TriageBot on a single message. Returns the full state."""
    initial: BotState = {
        "message":       message,
        "route":         None,
        "tool_result":   None,
        "draft":         None,
        "review_result": None,
        "review_reason": None,
        "final_reply":   None,
        "retry_count":   0,
        "path_log":      [],
    }
    result = graph.invoke(initial)
    return result
