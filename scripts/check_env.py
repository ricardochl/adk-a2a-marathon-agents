"""Check that your environment is ready for the workshop.

Run it before starting (and ask every attendee to run it):

    uv run python scripts/check_env.py                # everything, incl. 1 call per model
    uv run python scripts/check_env.py --skip-models  # no Gemini calls (free)

Exits with status 1 when something would block the workshop.
"""

from __future__ import annotations

import argparse
import importlib.metadata as md
import importlib.util
import os
import pathlib
import socket
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:  # reported below as a missing dependency
    pass

failures: list[str] = []
warnings: list[str] = []


def ok(msg: str) -> None:
    print(f"  ✔ {msg}")


def warn(msg: str, fix: str = "") -> None:
    warnings.append(msg)
    print(f"  ! {msg}" + (f"\n      → {fix}" if fix else ""))


def fail(msg: str, fix: str = "") -> None:
    failures.append(msg)
    print(f"  ✘ {msg}" + (f"\n      → {fix}" if fix else ""))


def section(title: str) -> None:
    print(f"\n{title}")


def major_minor(pkg: str) -> tuple[int, int] | None:
    try:
        parts = md.version(pkg).split(".")
        return int(parts[0]), int(parts[1])
    except Exception:
        return None


def check_python() -> None:
    section("Python")
    v = sys.version_info
    if v >= (3, 10):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        fail(f"Python {v.major}.{v.minor} is too old", "Python 3.10 or newer is required")


def check_env_file() -> list[str]:
    section("Configuration (.env)")
    if not (ROOT / ".env").exists():
        fail("No .env file", "cp .env.example .env  and set your project ID")
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    if not project or project.startswith("<"):
        fail("GOOGLE_CLOUD_PROJECT is not set", "Edit .env with your project ID")
    else:
        ok(f"Project: {project}")

    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
    models = [
        os.environ.get("PLANNER_MODEL", "gemini-3-flash-preview"),
        os.environ.get("EVALUATOR_MODEL", "gemini-3.1-pro-preview"),
        os.environ.get("SIMULATOR_MODEL", "gemini-3-flash-preview"),
    ]
    if any(m.startswith("gemini-3") for m in models) and location != "global":
        fail(f"GOOGLE_CLOUD_LOCATION={location} with Gemini 3 models",
             "Gemini 3 models are served from 'global': set GOOGLE_CLOUD_LOCATION=global")
    else:
        ok(f"Model location: {location}")

    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() != "true":
        warn("GOOGLE_GENAI_USE_VERTEXAI is not 'true'", "Without it ADK tries the AI Studio API")

    if os.environ.get("AGENT_ENGINE_ID") and os.environ.get("AGENT_ENGINE_LOCATION", "") in ("", "global"):
        warn("AGENT_ENGINE_ID set without a regional AGENT_ENGINE_LOCATION",
             "Agent Engine is regional: e.g. AGENT_ENGINE_LOCATION=us-central1")

    if os.environ.get("EVALUATOR_MODE", "vertex") == "heuristic":
        warn("EVALUATOR_MODE=heuristic: the Evaluator will not use the LLM judges")
    return list(dict.fromkeys(models))


def check_dependencies() -> None:
    section("Dependencies (tested versions)")
    rules = {
        "google-adk": ((1, 25), (2, 0)),
        "a2a-sdk": ((0, 3), (0, 4)),
        "google-cloud-aiplatform": ((1, 121), (2, 0)),
    }
    for pkg, (low, high) in rules.items():
        v = major_minor(pkg)
        if v is None:
            fail(f"{pkg} is not installed", "uv sync")
        elif not (low <= v < high):
            fail(f"{pkg} {md.version(pkg)} is outside the tested range",
                 "Install from the lockfile: uv sync (not a bare pip install)")
        else:
            ok(f"{pkg} {md.version(pkg)}")
    if importlib.util.find_spec("starlette") is None:
        fail("starlette is missing (a2a-sdk[http-server])", "uv sync")


def check_agents() -> None:
    section("Agents and tools")
    try:
        from src.planner_agent.evaluator.agent import root_agent as _evaluator  # noqa: F401
        ok("Evaluator builds")
    except Exception as e:
        fail(f"Evaluator does not build: {type(e).__name__}: {e}")
    try:
        from src.simulator_agent.agent.agent import root_agent as _simulator  # noqa: F401
        ok("Simulation Controller builds")
    except Exception as e:
        fail(f"Simulation Controller does not build: {type(e).__name__}: {e}")
    try:
        from src.planner_agent.agent.agent import root_agent as planner
        names = [getattr(t, "name", None) or type(t).__name__ for t in planner.tools]
        if "plan_marathon_route" in names:
            ok("Planner builds with plan_marathon_route")
        else:
            fail("Planner has no plan_marathon_route tool",
                 "src/planner_agent/skills/route-planning/tools.py is missing")
    except Exception as e:
        fail(f"Planner does not build: {type(e).__name__}: {e}")

    try:
        path = ROOT / "src/planner_agent/skills/route-planning/tools.py"
        spec = importlib.util.spec_from_file_location("route_tools", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        km = mod.plan_marathon_route("Las Vegas")["distance_km"]
        (ok if abs(km - 42.195) < 0.01 else fail)(f"Sample route: {km} km")
    except Exception as e:
        fail(f"plan_marathon_route fails: {e}")


def check_ports() -> None:
    section("Ports")
    for port, who in ((8084, "Planner"), (8089, "Simulator")):
        with socket.socket() as s:
            s.settimeout(0.5)
            busy = s.connect_ex(("127.0.0.1", port)) == 0
        if busy:
            warn(f"{port} ({who}) is already in use",
                 "If it is an old workshop server: pkill -f local_server")
        else:
            ok(f"{port} ({who}) is free")


def check_credentials() -> bool:
    section("Credentials")
    try:
        from google.auth import default
        _, adc_project = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        ok(f"Application Default Credentials (ADC project: {adc_project or 'n/a'})")
        return True
    except Exception as e:
        fail(f"No credentials: {type(e).__name__}",
             "gcloud auth application-default login   (Cloud Shell already has them)")
        return False


def check_models(models: list[str]) -> None:
    section("Models (one minimal call per model)")
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        fail("Cannot import google.genai", "uv sync")
        return
    client = genai.Client(
        vertexai=True,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
    )
    for model in models:
        try:
            client.models.generate_content(
                model=model, contents="Reply with: ok",
                config=types.GenerateContentConfig(max_output_tokens=16),
            )
            ok(f"{model} responds")
        except Exception as e:
            text = str(e)
            if "404" in text:
                fix = ("Check GOOGLE_CLOUD_LOCATION=global and that your project can use this "
                       "model; otherwise change *_MODEL in .env (e.g. gemini-2.5-flash)")
            elif "403" in text or "PERMISSION" in text.upper():
                fix = "gcloud services enable aiplatform.googleapis.com and check billing"
            elif "429" in text or "RESOURCE_EXHAUSTED" in text:
                fix = "Quota exhausted: wait or use another model"
            else:
                fix = ""
            fail(f"{model}: {text[:140]}", fix)


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-workshop environment check")
    parser.add_argument("--skip-models", action="store_true", help="Do not call Gemini")
    args = parser.parse_args()

    print("Environment check · Multi-agent marathon planner")
    check_python()
    models = check_env_file()
    check_dependencies()
    check_agents()
    check_ports()
    has_credentials = check_credentials()
    if args.skip_models:
        print("\n(Models: skipped with --skip-models)")
    elif has_credentials and not any("GOOGLE_CLOUD_PROJECT" in f for f in failures):
        check_models(models)

    print("\n" + "─" * 60)
    if failures:
        print(f"✘ {len(failures)} problem(s) to fix, {len(warnings)} warning(s).")
        return 1
    print(f"✔ Ready for the workshop ({len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
