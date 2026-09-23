"""
00 · Setup check  —  RUN THIS FIRST.

Confirms that your environment is ready:
  1. Your .env has a valid API key for your chosen provider.
  2. The LLMClient can reach the model and get a reply.

Run it from the Week 1 folder:
    python skeleton/00_setup_check.py

If you see a green success line, you're ready for the rest of Week 1.
"""

import sys
import os

# Make the local `utils` package importable no matter where you run from.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.llm_client import LLMClient


def main():
    print("=" * 60)
    print(" BITS Agentic AI — Week 1 · Setup Check")
    print("=" * 60)

    try:
        client = LLMClient()
    except Exception as e:
        print(f"\n[X] Could not create the LLM client: {e}")
        print("    -> Check LLM_PROVIDER and the matching *_API_KEY in your .env.")
        return

    print(f"\nProvider : {client.provider}")
    print(f"Model    : {client._default_model()}")
    print("\nSending a test message to the model...\n")

    reply = client.get_completion(
        "In one short sentence, welcome a new AI engineering student to the course."
    )

    if reply:
        print("[OK] Success! The model replied:\n")
        print("   ", reply.strip())
        print("\nYour environment is ready. On to 01_assistant_vs_agent.py!")
    else:
        print("[X] No reply received.")
        print("    -> Check your API key, internet connection, and provider in .env.")
        print("    -> See SETUP.md for provider-specific help.")


if __name__ == "__main__":
    main()
