# TriageBot — NimbusPay Support Agent

A self-reviewing AI support agent built with **LangChain + LangGraph + Groq**.

## Live Demo
🔗 Deploy on Streamlit Cloud (see below)

## Architecture

```
[Customer Message]
       ↓
   classify         ← LLM decides: faq | tool | escalate
       ↓
 ┌─────┴──────────────┐
faq_node  tool_node  escalate_node
 └─────┬──────────────┘
       ↓
  draft_node         ← LLM writes a reply
       ↓
  review_node        ← checks draft against rules
       ↓
  pass? ──yes──→ respond → [Customer sees reply]
   │
  no (retry < 3)
   ↓
  redo_node          ← LLM rewrites draft
   └──────────────→ review_node  (loop)
```

## Tools
| Tool | What it does |
|------|-------------|
| `faq_lookup` | Searches 8-item FAQ by similarity |
| `account_lookup` | Returns balance + last transaction |
| `refund_calculator` | Auto-approves ≤$50, escalates >$50 |
| `open_ticket` | (Bonus) Opens a support ticket |

## Setup & Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/triagebot
cd triagebot
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
streamlit run app.py
```

## Deploy to Streamlit Cloud (Free Live URL)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → set main file as `app.py`
4. Add secret: `GROQ_API_KEY = "your_key"`
5. Click **Deploy** → get your live URL!

## Project Structure
```
triagebot/
├── app.py            ← Streamlit web UI
├── agent.py          ← LangGraph graph (nodes, routing, loop)
├── tools.py          ← 4 LangChain tools
├── data.py           ← Synthetic FAQ + accounts
├── requirements.txt
└── .streamlit/
    └── config.toml   ← UI theme
```

## Why LangChain + LangGraph?
- **LangChain** → LLM interface, prompt templates, and tools
- **LangGraph** → stateful graph: branching, redo loop with retry cap, state management
