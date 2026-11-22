# Correcciones respecto del codelab

Qué cambia este repo frente al código del codelab, por qué, y en qué etiqueta
aparece. Para quien imparte el taller: léelo una vez antes de presentar.

Leyenda de la columna **Verificado**:

- **aquí**: reproducido y probado en este repo (instalación limpia, servidores locales, tests).
- **pendiente**: la corrección está aplicada, pero depende del comportamiento
  de Vertex AI real y necesita un proyecto de Google Cloud para confirmarse.
  Confírmalo con `scripts/check_env.py` y una corrida de
  `scripts/send_request.py` el día anterior.

## 1. Instalación

| # | Problema | Corrección | Etiqueta | Verificado |
|---|---|---|---|---|
| 1.1 | Con dependencias `>=` se instala a2a-sdk 1.x: desaparecen `a2a.server.apps`, `TextPart`, `ServerError`… y ningún servidor A2A arranca | `a2a-sdk[http-server]>=0.3.9,<0.4` | step-03 | aquí |
| 1.2 | Sin el extra `[http-server]` falta starlette y `A2AStarletteApplication` no se importa | El extra está en `pyproject.toml` | step-03 | aquí |
| 1.3 | Con ADK 2.x cambia la firma de `RemoteA2aAgent._resolve_agent_card_from_url()` y el override del codelab rompe la conexión al Simulator | `google-adk>=1.25.0,<2` | step-03 | aquí |
| 1.4 | `google-cloud-aiplatform` también sube de versión mayor | `>=1.121.0,<2` | step-03 | aquí |
| 1.5 | Cada asistente resolvería versiones distintas | `uv.lock` versionado; instalar siempre con `uv sync` | step-03 | aquí |

Versiones resueltas: google-adk 1.39.1 · a2a-sdk 0.3.26 · google-cloud-aiplatform 1.165.1.

## 2. Región y modelos

| # | Problema | Corrección | Etiqueta | Verificado |
|---|---|---|---|---|
| 2.1 | Los modelos Gemini 3 (`gemini-3-flash-preview`, `gemini-3.1-pro-preview`) se sirven desde `global`; con `us-central1`, la primera llamada da 404 | `GOOGLE_CLOUD_LOCATION=global` en `.env.example` y como valor por defecto en el código | step-03 | pendiente |
| 2.2 | Con `global`, los servicios de Agent Engine (sesiones, Memory Bank) heredarían una región que no les sirve | Variable separada `AGENT_ENGINE_LOCATION` (por defecto `us-central1`) | step-03 | aquí (código) |

## 3. Evaluador

| # | Problema | Corrección | Etiqueta | Verificado |
|---|---|---|---|---|
| 3.1 | El prompt de `MetricPromptBuilder` pide una justificación en prosa, pero el servicio de evaluación lee la respuesta del juez como JSON: los seis jueces fallan con `400 INVALID_ARGUMENT` | `judge_model_system_instruction` con un contrato JSON (`{"score", "explanation"}`) en cada métrica | step-04 | pendiente (el campo existe en el SDK fijado: aquí) |
| 3.2 | Un juez sin puntaje se contaba como 50: seis jueces caídos daban un "plan mediocre" de 52.5 etiquetado como `vertex_ai_eval` | Si falta un puntaje, se usa la heurística y `eval_method` dice `heuristic_fallback`, con `eval_error` | step-04 | aquí (tests) |
| 3.3 | Con siete explicaciones largas, el `EvaluationResult` se cortaba con `max_output_tokens=4096` | 8192 tokens y cada hallazgo recortado a 400 caracteres | step-04 | aquí (tests) / pendiente (en vivo) |
| 3.4 | `tools.py` importa de `agent.py` y `agent.py` de `tools.py`; un `except Exception` en `__init__.py` ocultaba cualquier error y el paquete quedaba sin `root_agent` | Constantes en `evaluator/config.py`; los `__init__.py` ya no tragan errores | step-04 | aquí |
| 3.5 | En vivo, los jueces pueden tardar minutos | `EVALUATOR_MODE=heuristic` salta los jueces sin tocar código | step-04 | aquí |

## 4. A2A y herramientas

| # | Problema | Corrección | Etiqueta | Verificado |
|---|---|---|---|---|
| 4.1 | La tarjeta del Simulator anuncia `http://localhost:9999/` y transporte HTTP+JSON (valores por defecto de `create_agent_card`): el Planner manda los mensajes a un puerto vacío | `url = http://127.0.0.1:8089` y transporte JSON-RPC | step-07 | aquí |
| 4.2 | ADK exige que la URL de la tarjeta tenga el mismo origen desde el que se descargó (`127.0.0.1` ≠ `localhost`) | Se usa `127.0.0.1` | step-07 | aquí |
| 4.3 | El codelab carga `plan_marathon_route` de `skills/route-planning/tools.py`, pero nunca da ese archivo: el Planner arranca sin herramienta de rutas y el modelo inventa la ruta | Implementación propia: red sintética + Dijkstra + ajuste a 42.195 km + GeoJSON con agua y carpas médicas | step-06 | aquí |
| 4.4 | Los `SKILL.md` citan `references/` que no existen | `marathon_planning_guide.md`, `evaluation_criteria.md`, `readiness_checklist.md` | step-05/06 | aquí |
| 4.5 | El paso final solo hace `curl` a la tarjeta: nadie ve al sistema funcionar | `scripts/send_request.py` envía un `message/send` real | step-07 | aquí |
| 4.6 | Los logs "Added … tool" se emiten antes de configurar el logging y no se ven; al reiniciar sin la variable, nada avisa que volviste a modo Solo | El servidor imprime herramientas, `Mode:` y región de modelos | step-07 | aquí |

## 5. Lo que este repo no resuelve

- **Memory Bank no se demuestra** en local: sin `AGENT_ENGINE_ID` todo usa
  sesiones en memoria y `auto_save_memories` no hace nada. Preséntalo como "la
  línea que cambias para producción", no como algo que está funcionando.
- **La ruta es sintética**: una cuadrícula de calles, no un trazado real ni
  certificado.
- **El pipeline completo contra Vertex AI no se corrió desde aquí.** Los tests
  y los servidores locales sí; la llamada a Gemini y a Vertex AI Evaluation
  necesitan tu proyecto.
