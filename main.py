"""
TriageBot CLI — NimbusPay Support Agent
Usage:  python main.py
        python main.py --demo
"""

import sys
import os
from agent import run

DIVIDER = "─" * 60

def print_result(result: dict):
    print(f"\n{DIVIDER}")
    print(f"🤖  TriageBot Reply:\n    {result['final_reply']}")
    print(f"\n📍  Path taken:")
    for step in result["path_log"]:
        print(f"    → {step}")
    if result["tool_result"]:
        print(f"\n🔧  Tool result:\n    {result['tool_result']}")
    if result["retry_count"] > 0:
        print(f"\n🔄  Review loop fired {result['retry_count']} time(s)")
    print(DIVIDER)


DEMO_MESSAGES = [
    ("FAQ",       "Why was I charged a $2 fee?"),
    ("Tool",      "What's the balance on account 4821?"),
    ("Escalate",  "I want a $120 refund, this is outrageous!"),
    ("Loop",      "Give me a $200 refund immediately and promise it's done."),
]

def run_demo():
    print("\n" + "═" * 60)
    print("  🏦  TriageBot Demo — NimbusPay Support Agent")
    print("═" * 60)
    for label, msg in DEMO_MESSAGES:
        print(f"\n[{label}] Customer: \"{msg}\"")
        result = run(msg)
        print_result(result)
        input("\nPress Enter for next message...")


def run_cli():
    print("\n🏦  NimbusPay TriageBot  (type 'quit' to exit)\n")
    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if msg.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not msg:
            continue
        result = run(msg)
        print_result(result)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_demo()
    else:
        run_cli()
