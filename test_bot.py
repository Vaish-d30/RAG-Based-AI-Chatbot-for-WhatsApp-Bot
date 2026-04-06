#!/usr/bin/env python3
"""
test_bot.py — Test the COMMANDO RAG chatbot locally in your terminal.
No WhatsApp setup needed. Great for development and demos.

Usage:
    python test_bot.py
    python test_bot.py --user alice
    python test_bot.py --model gemini-1.5-pro
"""

import argparse
import logging
import os
import sys

logging.basicConfig(level=logging.WARNING)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Test COMMANDO RAG Bot locally")
    parser.add_argument("--user",  default="test_user", help="Simulated user ID")
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "gemini-2.5-flash"))
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  COMMANDO Networks RAG Chatbot — Local Test")
    print("="*60)
    print(f"  User : {args.user}")
    print(f"  Model: {args.model}")
    print("  Commands: 'quit' to exit | 'reset' to clear history")
    print("="*60 + "\n")

    # Load pipeline
    print("Loading RAG pipeline...", end=" ", flush=True)
    from rag_pipeline.rag_chain import load_pipeline
    pipeline = load_pipeline(
        docs_path=os.getenv("DOCS_PATH", "data/processed/documents.json"),
        llm_model=args.model,
    )
    print("ready ✓\n")

    # Sample conversation to demo context retention
    demo_mode = "--demo" in sys.argv
    if demo_mode:
        demo_queries = [
            "Which switches support stacking?",
            "What are the different models available in it?",
            "What is the PoE budget on the 24-port version?",
            "Does it support VLAN?",
        ]
        print("🎬 Running demo conversation...\n")
        for q in demo_queries:
            print(f"You: {q}")
            reply = pipeline.generate_response(args.user, q)
            print(f"Bot: {reply}\n")
            print("-" * 40 + "\n")
        return

    # Interactive loop
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Bot: Goodbye! 👋")
            break
        if user_input.lower() in ["reset", "clear"]:
            pipeline.reset_conversation(args.user) 
            print("Bot: Conversation cleared. Ask me anything!\n")
            continue

        reply = pipeline.generate_response(args.user, user_input)
        print(f"\nBot: {reply}\n")


if __name__ == "__main__":
    main()
