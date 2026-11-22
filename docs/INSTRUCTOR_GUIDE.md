# Guía para quien imparte el taller

La presentación es corta (11 diapositivas, unos 20 minutos). El resto del
tiempo es práctica guiada sobre este repo.

## El día anterior

1. En un proyecto **nuevo**, con facturación: clona, `uv sync`, `cp .env.example .env`.
2. `uv run python scripts/check_env.py` hasta que diga **Ready for the workshop**.
3. Levanta Simulator y Planner en modo Equipo completo y corre una vez
   `uv run python scripts/send_request.py`. Anota cuánto tarda: es tu margen de paciencia en vivo.
4. Si la evaluación tarda demasiado o falla, revisa `eval_method` y `eval_error`
   en la respuesta (ver `docs/FIXES.md`, sección 3).
5. Revisa que la URL del repo de la última diapositiva sea la correcta.

Mensaje para los asistentes, enviado antes del taller:

> Trae un proyecto de Google Cloud con facturación. Antes de llegar: clona
> `https://github.com/ricardochl/adk-a2a-marathon-agents`, corre `uv sync` (descarga bastante) y luego
> `uv run python scripts/check_env.py --skip-models`. Fuera de Cloud
> Shell, ejecuta también `gcloud auth application-default login`.

## Guion

| Min | Diapositivas | Qué hacer |
|---:|---|---|
| 0–5 | 1–3 | Qué construimos y la arquitectura: una conexión local (AgentTool) y una remota (A2A). |
| 5–15 | 4–5 | Preparación en vivo. Todos corren `check_env.py`. Explica por qué fijamos versiones y la región `global`. |
| 15–35 | 6 | Evaluador. `git checkout step-04`, abre `evaluator/tools.py`: una métrica, el contrato JSON del juez, el respaldo heurístico. Corre `uv run pytest tests/test_evaluator_contract.py -q`. |
| 35–45 | 7 | Simulator y ADK Skills. `git checkout step-05`. |
| 45–60 | 8 | Planner: SkillToolset, AgentTool y RemoteA2aAgent. `git checkout step-06`; muestra `plan_marathon_route("Madrid")` en un REPL. |
| 60–80 | 9–10 | `git checkout main`. Modo Solo, luego Equipo completo (mira la línea `Mode:`). Cada quien envía su pedido con `send_request.py`. |
| 80–90 | 11 | Limpieza y preguntas. |

## Si algo falla en vivo

| Síntoma | Qué hacer |
|---|---|
| La evaluación tarda minutos | Reinicia el Planner con `EVALUATOR_MODE=heuristic` y explica que el respaldo es parte del diseño |
| `Mode: SOLO` con el Simulator corriendo | Faltó `SIMULATOR_AGENT_RESOURCE_NAME=local:8089` al reiniciar |
| `404` de modelo | `GOOGLE_CLOUD_LOCATION=global`, o cambia `*_MODEL` a `gemini-2.5-flash` |
| `eval_method: heuristic_fallback` | Los jueces fallaron; `eval_error` dice por qué |
| `uv sync` muy lento (wifi del lugar) | Que trabajen en parejas sobre una máquina que ya instaló |

## Tres momentos para no saltarse

1. **El juez como contrato.** "LLM como juez" no es solo una rúbrica: también
   es el formato que el juez devuelve y lo que el servicio sabe leer. El codelab
   escribió la rúbrica pero no el formato.
2. **Un promedio alto que no aprueba.** `test_high_severity_blocks_pass_even_with_high_average`:
   más de 90 de promedio y aun así reprueba por un hallazgo grave.
3. **Una variable de entorno cambia la topología.** El mismo código pasa de dos
   a tres agentes con `SIMULATOR_AGENT_RESOURCE_NAME`, y con un nombre de
   recurso de Agent Engine apuntaría a la nube.
