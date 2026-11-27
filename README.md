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
Iteration: OFF · single evaluation (set PLANNER_REVISIONS=1 to turn it on)
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

### Iterar un plan que no aprobó

El Evaluator aprueba con 85 o más, así que lo normal es que el primer plan
**no apruebe**. Hay dos formas de iterar.

#### A. Automática: el Planner se corrige solo

Con `PLANNER_REVISIONS`, si el plan no aprueba, el Planner lo corrige usando los
hallazgos del Evaluator y lo vuelve a enviar, hasta N veces. Se detiene en
cuanto una ronda aprueba. El Simulator revisa solo la versión final.

| Valor | Qué hace | Tiempo y costo aprox. |
|---|---|---|
| `0` (por defecto) | Una sola evaluación, como en el codelab | 1× |
| `1` | Hasta 1 corrección → máximo 2 evaluaciones | hasta 2× |
| `2` | Hasta 2 correcciones → máximo 3 evaluaciones | hasta 3× |
| `3` | Máximo permitido (valores mayores se limitan a 3) | hasta 4× |

**Encenderla solo para este arranque** (recomendado en clase, porque se ve en el
comando):

```bash
PLANNER_REVISIONS=1 uv run python -m src.planner_agent.runtime.local_server

# con el Simulator (Equipo completo)
PLANNER_REVISIONS=1 SIMULATOR_AGENT_RESOURCE_NAME=local:8089 uv run python -m src.planner_agent.runtime.local_server
```

**Dejarla fija:** en `.env` cambia `PLANNER_REVISIONS=0` por el valor que quieras:

```bash
sed -i 's/^PLANNER_REVISIONS=.*/PLANNER_REVISIONS=1/' .env
```

**Comprobar que está encendida:** el banner del Planner dice
`Iteration: ON · up to 1 revision(s), 2 evaluations max`. Con `OFF` está apagada.

**Apagarla:** arranca con `PLANNER_REVISIONS=0`, o vuelve a poner `0` en `.env`.
Cualquier cambio necesita reiniciar el Planner (`Ctrl+C` y arrancarlo de nuevo).

**Qué cambia en la respuesta:** al final aparece una tabla con la nota de cada
ronda y qué se corrigió en cada una. La nota que cuenta es la de la última ronda.

Cada ronda es otra evaluación completa con los 6 jueces, así que un pedido con
`PLANNER_REVISIONS=1` puede tardar 3–4 minutos. `send_request.py` espera hasta
10 minutos; para más, usa `--timeout 900`.

**Cambiar cómo itera:** las reglas de la iteración están en
`src/planner_agent/agent/prompts.py` (función `_iteration_rules`): por ejemplo,
qué debe mostrar en la tabla o qué puede cambiar en cada ronda. El máximo de
rondas está en `MAX_REVISIONS` de `src/planner_agent/agent/config.py`, y la nota
para aprobar en `PASS_THRESHOLD` de `src/planner_agent/evaluator/config.py`.
Bajar esa nota hace que más planes "aprueben", pero no los mejora.

#### B. A mano: le reenvías el plan con sus críticas

Cada pedido es una conversación nueva, así que el Planner no recuerda el plan
anterior: hay que mandárselo.

```bash
# 1. Guarda la respuesta
uv run python scripts/send_request.py --file pedido.txt | tee resultado1.txt

# 2. Arma el pedido de iteración con el plan anterior adentro
{
  echo "Mejora este plan de maratón. Corrige los hallazgos del Evaluator y los bloqueos del Simulator que aparecen al final. Mantén lo que ya está bien. Después evalúalo y revisa la simulación otra vez."
  echo
  echo "--- PLAN ANTERIOR Y SUS RESULTADOS ---"
  cat resultado1.txt
} > iteracion.txt

# 3. Envíalo
uv run python scripts/send_request.py --file iteracion.txt | tee resultado2.txt
```

Puedes abrir `iteracion.txt` en el editor y agregar indicaciones concretas
("detalla los ingresos por patrocinador"). Mientras más específicas, más sube la
nota.

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
| `Address already in use` | `pkill -f local_server` (ver "Detener y limpiar") |
| `eval_method: heuristic_fallback` | Los jueces fallaron; el motivo está en `eval_error` |
| `Connection refused` / `No A2A server at …` | El servidor no está corriendo: levántalo en otra pestaña |
| `Iteration: OFF` aunque pusiste `PLANNER_REVISIONS` | Reinicia el Planner; la variable solo se lee al arrancar |
| `PLANNER_REVISIONS must be a whole number` | Usa un número entero de 0 a 3 |
| `send_request.py` corta por tiempo con la iteración encendida | `uv run python scripts/send_request.py --timeout 900 …` |

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

## Detener y limpiar

### 1. Detener los servidores

Lo normal es `Ctrl+C` en la pestaña de cada servidor. Para detener **todos** de
una vez, desde cualquier pestaña:

```bash
pkill -f local_server
```

Comprueba que los puertos quedaron libres (Planner `8084`, Simulator `8089`). Si
no imprime nada, están libres:

```bash
ss -ltnp | grep -E '8084|8089'
```

Si alguno sigue ocupado:

```bash
fuser -k 8084/tcp 8089/tcp     # cierra lo que use esos puertos
pkill -9 -f local_server       # último recurso: un proceso colgado
```

Es lo que hay que hacer cuando aparece `Address already in use`, y antes de
reiniciar el Planner tras un `git pull` o un cambio de variables.

### 2. Borrar los archivos generados

Las pruebas dejan archivos sueltos en la carpeta del repo (`route.geojson`,
`resultado1.txt`, `iteracion.txt`, `pedido.txt`, `demo_resultado.txt`…):

```bash
git clean -n     # muestra qué se borraría, sin borrar nada
git clean -f     # borra los archivos que git no conoce
```

`git clean` no toca `.env` ni `.venv`, porque están en `.gitignore`. Pero sí
borra tus pedidos y resultados: si quieres conservar alguno, cópialo fuera de la
carpeta antes (por ejemplo, `cp pedido.txt ~/`).

### 3. Volver el código al estado original

Si modificaste archivos (por ejemplo, haciendo los ejercicios) y quieres empezar
de nuevo:

```bash
git status                   # qué cambiaste
git stash                    # guarda tus cambios aparte, por si los quieres después
# o, para descartarlos definitivamente:
git restore .
git checkout main && git pull
```

### 4. Rehacer la configuración y el entorno

```bash
# .env desde cero
cp .env.example .env && sed -i "s/<YOUR_PROJECT_ID>/$(gcloud config get project)/" .env

# entorno de Python desde cero (si algo quedó roto)
rm -rf .venv && uv sync
```

### 5. Borrar todo el taller de Cloud Shell

El disco de Cloud Shell es pequeño (5 GB) y se conserva entre sesiones:

```bash
pkill -f local_server
cd ~ && rm -rf ~/adk-a2a-marathon-agents
uv cache clean               # caché de paquetes de uv
```

### 6. Recursos en Google Cloud

El taller solo hace llamadas a la API de Vertex AI: no deja máquinas, bases de
datos ni agentes desplegados cobrando. Lo único que se cobra son las llamadas a
Gemini que hiciste. Si creaste un proyecto solo para esto, bórralo:

```bash
gcloud projects delete $(gcloud config get project)
```

Si el proyecto es tuyo y lo vas a seguir usando, puedes dejarlo así o apagar la
API: `gcloud services disable aiplatform.googleapis.com`.

## Créditos y licencia

Código de los agentes adaptado del codelab de Google, publicado bajo
[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0); contenido del codelab
bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
