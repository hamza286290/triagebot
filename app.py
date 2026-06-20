"""
TriageBot — Streamlit Web Interface
"""

import streamlit as st
import os
from agent import run

st.set_page_config(
    page_title="TriageBot — NimbusPay Support",
    page_icon="🏦",
    layout="centered"
)

# ── Styles ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main { background-color: #f8fafc; }
.stChatMessage { border-radius: 12px; }
.path-box {
    background: #f1f5f9;
    border-left: 4px solid #6366f1;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    color: #475569;
    margin-top: 8px;
}
.tool-box {
    background: #f0fdf4;
    border-left: 4px solid #22c55e;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    color: #166534;
    margin-top: 6px;
}
.retry-box {
    background: #fff7ed;
    border-left: 4px solid #f97316;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    color: #9a3412;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────────
st.title("🏦 TriageBot")
st.caption("NimbusPay AI Support Agent · Powered by LangChain + LangGraph + Groq")

# ── API Key input (if not in env) ────────────────────────────────────────────────
if not os.environ.get("GROQ_API_KEY"):
    with st.sidebar:
        st.header("🔑 Setup")
        key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
        if key:
            os.environ["GROQ_API_KEY"] = key
            st.success("Key set!")
        st.markdown("[Get a free key →](https://console.groq.com)")

# ── Sidebar info ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Try these messages")
    examples = [
        "Why was I charged a $2 fee?",
        "What's the balance on account 4821?",
        "I want a $120 refund!",
        "How do I reset my password?",
        "What's on account 3390?",
        "I want a $30 refund for a bad transaction.",
        "I need to speak to a human right now!",
        "Give me a $200 refund immediately.",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["pending_input"] = ex

    st.divider()
    st.markdown("**🗺️ Graph nodes:**")
    st.markdown("""
- `classify` → route message  
- `faq_node` → search FAQ  
- `tool_node` → call tools  
- `escalate_node` → human hand-off  
- `draft_node` → write reply  
- `review_node` → check rules  
- `redo_node` → rewrite if failed  
- `respond` → send to customer  
""")

# ── Chat history ──────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and "meta" in msg:
            meta = msg["meta"]
            with st.expander("🔍 Show agent details"):
                st.markdown(f'<div class="path-box">📍 <b>Path:</b><br>' +
                    "<br>".join(f"→ {s}" for s in meta["path_log"]) +
                    "</div>", unsafe_allow_html=True)
                if meta.get("tool_result"):
                    st.markdown(f'<div class="tool-box">🔧 <b>Tool result:</b><br>{meta["tool_result"]}</div>',
                        unsafe_allow_html=True)
                if meta.get("retry_count", 0) > 0:
                    st.markdown(f'<div class="retry-box">🔄 <b>Review loop fired {meta["retry_count"]} time(s)</b></div>',
                        unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────────────────────────────
pending = st.session_state.pop("pending_input", None)
user_input = st.chat_input("Type your message...") or pending

if user_input:
    if not os.environ.get("GROQ_API_KEY"):
        st.error("Please enter your Groq API key in the sidebar first.")
        st.stop()

    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Run TriageBot
    with st.chat_message("assistant"):
        with st.spinner("TriageBot is thinking..."):
            result = run(user_input)

        reply = result["final_reply"]
        st.write(reply)

        with st.expander("🔍 Show agent details"):
            st.markdown(f'<div class="path-box">📍 <b>Path:</b><br>' +
                "<br>".join(f"→ {s}" for s in result["path_log"]) +
                "</div>", unsafe_allow_html=True)
            if result.get("tool_result"):
                st.markdown(f'<div class="tool-box">🔧 <b>Tool result:</b><br>{result["tool_result"]}</div>',
                    unsafe_allow_html=True)
            if result.get("retry_count", 0) > 0:
                st.markdown(f'<div class="retry-box">🔄 <b>Review loop fired {result["retry_count"]} time(s)</b></div>',
                    unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "meta": result
    })
