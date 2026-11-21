"""Local A2A server for the Simulation Controller Agent.

Usage: uv run python -m src.simulator_agent.runtime.local_server
"""

import asyncio
import logging
import os

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import TransportProtocol
from dotenv import load_dotenv

load_dotenv()

AGENT_PORT = 8089


async def run_server():
    from .agent_card import create_simulation_controller_card
    from .agent_executor import SimulationControllerExecutor

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise ValueError("GOOGLE_CLOUD_PROJECT must be set.")

    print("=" * 60)
    print("Starting Simulation Controller Agent Local A2A Server")
    print("=" * 60)

    agent_card = create_simulation_controller_card()
    # Not in the codelab: create_agent_card() leaves url=http://localhost:9999/
    # and the HTTP+JSON transport. The Planner would send its A2A messages to
    # that URL and fail. As the Planner's server does, publish this server's
    # real URL and transport (JSON-RPC). Use 127.0.0.1 (not "localhost")
    # because ADK requires the card URL to share the origin the Planner
    # fetched the card from (http://127.0.0.1:8089/.well-known/...).
    agent_card.url = f"http://127.0.0.1:{AGENT_PORT}"
    agent_card.preferred_transport = TransportProtocol.jsonrpc
    executor = SimulationControllerExecutor()
    handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore())

    app = A2AStarletteApplication(agent_card=agent_card, http_handler=handler)
    config = uvicorn.Config(app.build(), host="127.0.0.1", port=AGENT_PORT, log_level="info", loop="none")

    print(f"Simulator A2A server: http://127.0.0.1:{AGENT_PORT}")
    print(f"Agent card: http://127.0.0.1:{AGENT_PORT}/.well-known/agent-card.json")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_server())
