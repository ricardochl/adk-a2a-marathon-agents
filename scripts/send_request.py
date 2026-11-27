"""Send an A2A request (JSON-RPC `message/send`) to a local agent and print
the response.

Not in the codelab: its last step only curls the agent card, so nobody sees
the multi-agent system actually run. This script exercises it end to end.

Usage:
    uv run python scripts/send_request.py
    uv run python scripts/send_request.py "Plan a fast marathon in Tegucigalpa for 8,000 runners in March, budget USD 1M"
    uv run python scripts/send_request.py --url http://127.0.0.1:8089 --file examples/sample_plan.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid

import httpx

DEFAULT_URL = "http://127.0.0.1:8084"
DEFAULT_PROMPT = (
    "Plan a scenic marathon in San Pedro Sula, Honduras, on 2027-03-14 for 10,000 runners. "
    "Budget: USD 1.5M. Pass Parque Central, the Cathedral, Mercado Guamilito and "
    "Estadio Olímpico Metropolitano, start early to avoid the heat, and keep hospital "
    "access open. Then evaluate the plan and check simulation readiness."
)


def build_payload(text: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": str(uuid.uuid4()),
                "parts": [{"kind": "text", "text": text}],
                "metadata": {"user_id": "workshop_user"},
            }
        },
    }


def extract_text(result: dict) -> str:
    """Pull human-readable text out of a Task or Message result."""
    chunks: list[str] = []
    for artifact in result.get("artifacts") or []:
        for part in artifact.get("parts", []):
            if part.get("kind") == "text" and part.get("text"):
                chunks.append(part["text"])
    if not chunks:
        for part in result.get("parts") or []:  # result is a Message
            if part.get("kind") == "text":
                chunks.append(part["text"])
    if not chunks:
        msg = (result.get("status") or {}).get("message") or {}
        for part in msg.get("parts", []):
            if part.get("kind") == "text":
                chunks.append(part["text"])
    return "\n".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prompt", nargs="?", default=None, help="Text to send to the agent")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"A2A server URL (default: {DEFAULT_URL})")
    parser.add_argument("--file", help="Read the text to send from a file")
    parser.add_argument("--timeout", type=float, default=600.0, help="Timeout in seconds (default: 600)")
    parser.add_argument("--raw", action="store_true", help="Print the full JSON response")
    args = parser.parse_args()

    text = open(args.file, encoding="utf-8").read() if args.file else (args.prompt or DEFAULT_PROMPT)

    try:
        card = httpx.get(f"{args.url}/.well-known/agent-card.json", timeout=10).json()
    except httpx.ConnectError:
        # Most common workshop mistake: running the client before (or instead
        # of) the server. Explain it instead of dumping a traceback.
        if args.url.rstrip("/").endswith(":8089"):
            start = "uv run python -m src.simulator_agent.runtime.local_server"
        else:
            start = ("uv run python -m src.planner_agent.runtime.local_server\n"
                     "      (Full Team: prefix it with SIMULATOR_AGENT_RESOURCE_NAME=local:8089\n"
                     "       and start the Simulator first in another tab)")
        print(f"✗ No A2A server at {args.url}.\n"
              f"  Start it in ANOTHER terminal tab, wait for 'Uvicorn running', then run this again:\n"
              f"      {start}")
        return 1
    print(f"→ Agent: {card.get('name')} ({args.url})")
    print(f"→ Sending: {text[:120]}{'…' if len(text) > 120 else ''}")
    print("  (the Planner can take 1–3 minutes: it designs, evaluates and validates)\n")

    started = time.time()
    resp = httpx.post(args.url, json=build_payload(text), timeout=args.timeout)
    resp.raise_for_status()
    body = resp.json()
    elapsed = time.time() - started

    if args.raw:
        print(json.dumps(body, indent=2, ensure_ascii=False))
        return 0

    if "error" in body:
        print(f"✗ JSON-RPC error: {body['error']}")
        return 1

    result = body.get("result", {})
    state = (result.get("status") or {}).get("state", "n/a")
    print(f"Task state: {state}   ({elapsed:.0f}s)\n")
    print(extract_text(result) or "(no text in the response; use --raw to see the JSON)")
    return 0 if state in ("completed", "n/a") else 1


if __name__ == "__main__":
    sys.exit(main())
