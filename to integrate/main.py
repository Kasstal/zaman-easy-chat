#!/usr/bin/env python3
import os
import sys
import json
import argparse
from typing import List, Dict, Any

# OpenAI SDK
from openai import OpenAI

from app.infrastructure.chatbot.orchestrator import chat_turn
from app.infrastructure.services.rag_service import rag


# Your app modules

# -----------------------------
# RAG ingestion (local .txt)
# -----------------------------

def read_txt_files(rag_dir: str) -> List[Dict[str, Any]]:
    """
    Read all .txt files from rag_dir and return docs ready for SimpleRAG.build().
    We'll chunk each file by double newline blocks and fall back to a max length.
    """
    docs = []
    doc_id = 0

    def chunk_paragraphs(text: str, max_len: int = 900):
        # split by blank lines first
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        for p in parts:
            if len(p) <= max_len:
                yield p
            else:
                # hard-split long blocks
                s = 0
                while s < len(p):
                    yield p[s:s+max_len]
                    s += max_len

    for root, _, files in os.walk(rag_dir):
        for f in files:
            if not f.lower().endswith(".txt"):
                continue
            fp = os.path.join(root, f)
            with open(fp, "r", encoding="utf-8") as fh:
                text = fh.read()
            base = os.path.relpath(fp, rag_dir)

            # very light title guess = filename
            title = os.path.splitext(os.path.basename(f))[0]

            # make chunks
            for chunk in chunk_paragraphs(text, max_len=900):
                docs.append({
                    "id": f"doc-{doc_id}",
                    "title": title,
                    "url": None,
                    "content": chunk
                })
                doc_id += 1

    return docs


def ingest_rag(rag_dir: str):
    docs = read_txt_files(rag_dir)
    if not docs:
        print(f"⚠️  No .txt files found under: {rag_dir}")
        return
    rag.build(docs)
    print(f"✅ Ingested {len(docs)} chunks from {rag_dir}")


# -----------------------------
# Chat helpers
# -----------------------------

def run_single_turn(client: OpenAI, user_id: str, message: str):
    """Send one user message through the orchestrator and print the final assistant reply."""
    messages = [{"role": "user", "content": message}]
    out = chat_turn(client, user_id, messages)
    print(out["assistant_message"])


def run_chat_loop(client: OpenAI, user_id: str):
    """
    Interactive REPL: every line is a new user turn passed to orchestrator.chat_turn.
    Tool-calls are handled inside chat_turn.
    """
    history: List[Dict[str, str]] = []
    print("💬 Chat mode. Type 'exit' or Ctrl+C to quit.")
    while True:
        try:
            user = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye.")
            break

        if user.lower() in {"exit", "quit"}:
            print("👋 Bye.")
            break

        history.append({"role": "user", "content": user})
        result = chat_turn(client, user_id, history)

        # Print assistant reply
        msg = result.get("assistant_message", "")
        print(f"\nAssistant: {msg}\n")

        # Keep only alternating user/assistant visible messages in the loop
        history.append({"role": "assistant", "content": msg})


# -----------------------------
# CLI
# -----------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Personal Finance Assistant CLI (RAG + tool-calling via orchestrator.py)"
    )
    parser.add_argument("--user-id", default="demo-user", help="User ID for the session")
    parser.add_argument("--rag-dir", default="data/rag", help="Directory with .txt docs for RAG")

    sub = parser.add_subparsers(dest="cmd", required=True)

    # ingest RAG
    sub.add_parser("ingest", help="Read local .txt and build in-memory RAG index")

    # one-off single turn
    p_once = sub.add_parser("once", help="Send a single message (non-interactive)")
    p_once.add_argument("message", nargs="+", help="Your message text")

    # interactive chat
    sub.add_parser("chat", help="Interactive chat loop (REPL)")

    args = parser.parse_args()

    # OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY is not set.")
        sys.exit(1)
    client = OpenAI(api_key=api_key)

    if args.cmd == "ingest":
        ingest_rag(args.rag_dir)

    elif args.cmd == "once":
        # Make sure RAG is ready (optional but recommended)
        if not rag.vocab:
            ingest_rag(args.rag_dir)
        msg = " ".join(args.message)
        run_single_turn(client, args.user_id, msg)

    elif args.cmd == "chat":
        # Make sure RAG is ready (optional but recommended)
        if not rag.vocab:
            ingest_rag(args.rag_dir)
        run_chat_loop(client, args.user_id)


if __name__ == "__main__":
    main()
