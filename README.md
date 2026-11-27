# 🏃 ADK · A2A Marathon Agents — Planificador de maratones multiagente con ADK y A2A

Repo del taller basado en el codelab de Google
**[Crea un planificador de maratones multiagente con el ADK y A2A](https://codelabs.developers.google.com/next26/dev-keynote/build-multi-agent-marathon-planner?hl=es-419)**,
con las correcciones necesarias para que funcione hoy de punta a punta.

Tres agentes de IA colaboran para planificar una maratón en una ciudad:

| Agente | Rol | Modelo | Cómo se conecta |
|---|---|---|---|
| **Marathon Planner** | Orquestador: diseña ruta, logística, presupuesto | `gemini-3-flash-preview` (thinking 2048) | Servidor A2A en `:8084` |
| **Evaluator** | Juez de calidad: 7 criterios con Vertex AI Evaluation | `gemini-3.1-pro-preview` (thinking 1024) | Subagente local vía `AgentTool` |
| **Simulation Controller** | Verifica que el plan esté listo para simular | `gemini-3-flash-preview` (thinking 0) | Agente remoto vía **A2A** en `:8089` |

```
          usuario / scripts/send_request.py
                        │  A2A (JSON-RPC)
                        ▼
              ┌───────────────────┐
              │  Marathon Planner │  :8084
              │  SkillToolset     │  route-planning, plan-evaluation
              │  plan_marathon_route (Dijkstra → GeoJSON)
              └───┬───────────┬───┘
     AgentTool    │           │   RemoteA2aAgent (A2A)
     (local)      ▼           ▼
          ┌────────────┐   ┌──────────────────────┐
          │ Evaluator  │   │ Simulation Controller│  :8089
          │ 6 jueces + │   │ ADK Skill +          │
          │ 1 regla    │   │ check_plan_readiness │
          └────────────┘   └──────────────────────┘
```

## Requisitos

- Proyecto de Google Cloud **con facturación habilitada** (costo estimado < USD 5)
- Cloud Shell (recomendado) o una máquina con Python ≥ 3.10, `gcloud` y [`uv`](https://docs.astral.sh/uv/)

## Puesta en marcha

```bash
# 1. Proyecto, API y facturación
gcloud config set project <YOUR_PROJECT_ID>
gcloud services enable aiplatform.googleapis.com
gcloud beta billing projects describe $(gcloud config get project)   # debe decir billingEnabled: true

# 2. uv (si no lo tienes)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# 3. Código y dependencias (versiones fijadas en uv.lock)
git clone https://github.com/ricardochl/adk-a2a-marathon-agents.git
cd adk-a2a-marathon-agents
uv sync

# 4. Variables de entorno
cp .env.example .env
sed -i "s/<YOUR_PROJECT_ID>/$(gcloud config get project)/" .env

# 5. Verificar que todo está listo
uv run python scripts/check_env.py
```

> **Fuera de Cloud Shell** necesitas credenciales de aplicación:
> `gcloud auth application-default login`

> **Región:** los modelos Gemini 3 se sirven desde `GOOGLE_CLOUD_LOCATION=global`
> (con `us-central1`, como en el codelab, dan 404). El `.env.example` ya lo trae así.

`check_env.py` revisa la configuración, las versiones, que los tres
agentes se construyan, los puertos, las credenciales y hace una llamada mínima a
cada modelo. Con `--skip-models` no hace llamadas (gratis).

> Si la facturación sale `billingEnabled: false`, vincula la cuenta de prueba
> donde canjeaste el crédito: `gcloud billing accounts list` y luego
> `gcloud billing projects link $(gcloud config get project) --billing-account=<ACCOUNT_ID>`.

## Cómo seguir el taller

Todo se trabaja en la rama `main`, que ya tiene el código completo y
funcionando. El codelab es el libro de texto: **léelo** para entender qué hace
cada agente y por qué, pero **no copies su código**, porque tal cual hoy no
funciona (ver [docs/FIXES.md](docs/FIXES.md)). En cada paso, lee la sección del
codelab, abre los archivos en el editor de Cloud Shell y corre la comprobación.

| Paso del codelab | Abre en el repo | Comprueba con |
|---|---|---|
| 3. Configura el proyecto | `pyproject.toml`, `.env.example` | `uv run python scripts/check_env.py` → `Ready for the workshop` |
| 4. Agente Evaluador | `src/planner_agent/evaluator/config.py` y `tools.py` | `uv run pytest tests/test_evaluator_contract.py -q` → `7 passed` |
| 5. Simulation Controller | `src/simulator_agent/agent/tools.py` y `skills/review-marathon-plan/SKILL.md` | Simulator en una pestaña y `uv run python scripts/send_request.py --url http://127.0.0.1:8089 --file examples/sample_plan.md` en otra |
| 6. Marathon Planner | `src/planner_agent/agent/tools.py`, `planner-instruction.md` y `skills/route-planning/tools.py` | `uv run pytest tests/test_deterministic.py -q -k route` → `15 passed` |
| 7. Implementa y prueba | `src/*/runtime/local_server.py` | Modo Solo y Equipo completo (sección siguiente) y un pedido con `send_request.py` |

**¿Terminaste antes o quieres practicar?** Hay cinco
[ejercicios opcionales](docs/EXERCISES.md) donde escribes código: darle más
peso a la seguridad, exigir un protocolo de calor, escribir una herramienta
nueva para el Planner, agregar tu ciudad y enseñarle al Planner a planificar
para el calor.

## Ejecutar

### Modo Solo (Planner + Evaluator)

```bash
uv run python -m src.planner_agent.runtime.local_server
```

Deberías ver:

```
Added local Evaluator tool
Tools: SkillToolset, preload_memory, plan_marathon_route, evaluator_agent
Mode: SOLO (Planner + Evaluator)
Model location: global · Evaluator: vertex
```

En otra pestaña:

```bash
uv run python scripts/send_request.py            # pedido de ejemplo (San Pedro Sula)
uv run python scripts/send_request.py "Planifica una maratón rápida en Tegucigalpa para 8,000 corredores en marzo, presupuesto USD 1M"
```

### Modo Equipo completo (los tres agentes vía A2A)

```bash
# Pestaña 2: Simulation Controller
uv run python -m src.simulator_agent.runtime.local_server

# Pestaña 1: Planner conectado al simulador
SIMULATOR_AGENT_RESOURCE_NAME=local:8089 uv run python -m src.planner_agent.runtime.local_server
```

La línea `Mode:` debe decir `FULL TEAM`. **Mismo código, otra
configuración**: el cambio de modo es solo la variable `SIMULATOR_AGENT_RESOURCE_NAME`.

Para probar el Simulator por separado:

```bash
uv run python scripts/send_request.py --url http://127.0.0.1:8089 --file examples/sample_plan.md
```

### Si la evaluación tarda demasiado

Los seis jueces LLM pueden tardar uno o dos minutos. Para una demo rápida:

```bash
EVALUATOR_MODE=heuristic uv run python -m src.planner_agent.runtime.local_server
```

La respuesta del Evaluador siempre indica qué método usó en `eval_method`:
`vertex_ai_eval`, `heuristic` (elegido) o `heuristic_fallback` (Vertex AI
Evaluation falló; el motivo está en `eval_error`).

### Tests (sin credenciales)

```bash
uv run pytest
```

Cubren la verificación de distancia, el contrato JSON de los jueces, el respaldo
cuando un juez no responde, la regla de aprobación, el checklist del simulador,
la herramienta de rutas (42.195 km exactos) y el caché de sesiones.

## Diferencias con el codelab

El código de los agentes es el del codelab; los cambios hacen que funcione con
las versiones actuales de las librerías y contra Vertex AI. Resumen:

| Cambio | Motivo |
|---|---|
| Versiones fijadas + `uv.lock` | Con `>=` hoy se instalan a2a-sdk 1.x, ADK 2.x y aiplatform 2.x, que rompen el código |
| `GOOGLE_CLOUD_LOCATION=global` | Los modelos Gemini 3 dan 404 en `us-central1` |
| Contrato JSON para los jueces | El juez respondía en prosa y Vertex AI Evaluation espera JSON |
| Sin puntajes inventados | Un juez caído contaba como 50; ahora se usa la heurística y se avisa |
| Tarjeta del Simulator en `127.0.0.1:8089` | `create_agent_card()` deja `localhost:9999` y el Planner no lo encuentra |
| `plan_marathon_route` implementada | El codelab la usa pero nunca da el código |

La lista completa, con el paso donde aparece cada corrección y qué se verificó
aquí, está en [docs/FIXES.md](docs/FIXES.md). Para impartir el
taller, ver [docs/INSTRUCTOR_GUIDE.md](docs/INSTRUCTOR_GUIDE.md).

## Solución de problemas

| Síntoma | Solución |
|---|---|
| `Your default credentials were not found` | `gcloud auth application-default login` (fuera de Cloud Shell) |
| `403 … aiplatform.googleapis.com` / API not enabled | `gcloud services enable aiplatform.googleapis.com` y revisa la facturación |
| `404` con un modelo `gemini-3*` | `GOOGLE_CLOUD_LOCATION=global`; si sigue, cambia `*_MODEL` a `gemini-2.5-flash` |
| `ImportError: … a2a.server.apps` / `starlette` | Instalaste sin el lockfile: ejecuta `uv sync` |
| `Mode: SOLO` con el Simulator corriendo | Faltó `SIMULATOR_AGENT_RESOURCE_NAME=local:8089` al arrancar el Planner |
| `AgentCardResolutionError … same origin` | Usa el `local_server.py` del Simulator de este repo |
| `Address already in use` | `pkill -f local_server` |
| `eval_method: heuristic_fallback` | Los jueces fallaron; el motivo está en `eval_error` |
| `Connection refused` / `No A2A server at …` | El servidor no está corriendo: levántalo en otra pestaña |

## Para rehacerlo en casa (opcional)

No hace falta durante el taller. Si quieres construir el proyecto desde cero
leyendo el codelab, cada paso es un commit con su etiqueta:

| Etiqueta | Paso del codelab | Qué contiene |
|---|---|---|
| `step-03` | 3. Configura el proyecto | Estructura, `config.py`, servicios de sesión y memoria, versiones fijadas |
| `step-04` | 4. Agente Evaluador | 7 métricas, contrato JSON del juez, evaluación híbrida |
| `step-05` | 5. Simulation Controller | Checklist determinístico + ADK Skill `review-marathon-plan` |
| `step-06` | 6. Marathon Planner | Skills, `AgentTool`, `SerializableRemoteA2aAgent`, tool de rutas |
| `step-07` | 7. Implementa y prueba | Tarjetas A2A, servidores locales, cliente, tests |

```bash
git checkout step-03              # empezar desde la estructura
git diff step-04 step-05 --stat   # ver qué archivos agrega el paso 5
git checkout main                 # volver a la versión completa
```

## Limpieza

`Ctrl+C` en cada pestaña. El taller solo hace llamadas a la API de Vertex AI (sin
recursos persistentes). Si creaste un proyecto solo para esto:

```bash
gcloud projects delete $PROJECT_ID
```

## Créditos y licencia

Código de los agentes adaptado del codelab de Google, publicado bajo
[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0); contenido del codelab
bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
