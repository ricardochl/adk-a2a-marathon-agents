# Guía para quien imparte el taller

La presentación es corta (12 diapositivas, unos 20 minutos). El resto del
tiempo es práctica guiada sobre este repo.

**Cómo se usan el repo y el codelab:** el codelab es el libro de texto (se
**lee** para entender qué hace cada agente y por qué); el repo es el código que
se **ejecuta**. Nadie copia código del codelab: tal cual, hoy no funciona (ver
`docs/FIXES.md`). Todo se trabaja en la rama `main`; las etiquetas `step-XX`
son opcionales (ver al final).

## El día anterior

Todo en **Cloud Shell**, con un proyecto que tenga facturación activa.

### 1. Instalar y configurar

```bash
cd ~
git clone https://github.com/ricardochl/adk-a2a-marathon-agents.git
cd adk-a2a-marathon-agents
uv sync
cp .env.example .env
sed -i "s/<YOUR_PROJECT_ID>/$(gcloud config get project)/" .env
uv run python scripts/check_env.py
```

Sigue hasta que `check_env.py` diga **Ready for the workshop**.

Para confirmar la facturación:
`gcloud beta billing projects describe $(gcloud config get project)` debe
mostrar `billingEnabled: true`.

### 2. Probar el sistema completo

Los agentes son **servidores**: se quedan corriendo en su propia pestaña y no
devuelven el control. El pedido se envía desde **otra** pestaña. En Cloud Shell,
el botón **+** de la barra de pestañas abre una terminal nueva; en cada una
entra primero a la carpeta con `cd ~/adk-a2a-marathon-agents`.

| Pestaña | Comando | Espera a ver |
|---|---|---|
| 1 · Simulator | `uv run python -m src.simulator_agent.runtime.local_server` | `Uvicorn running on http://127.0.0.1:8089` |
| 2 · Planner | `SIMULATOR_AGENT_RESOURCE_NAME=local:8089 uv run python -m src.planner_agent.runtime.local_server` | `Mode: FULL TEAM` y `Uvicorn running on http://127.0.0.1:8084` |
| 3 · Pedido | `uv run python scripts/send_request.py` | `Task state: completed` y el plan |

Anota cuánto tarda el pedido (suele ser de 1 a 3 minutos): es tu margen de
paciencia en vivo. En la respuesta, revisa `eval_method`: si dice
`heuristic_fallback`, los jueces fallaron y `eval_error` dice por qué
(`docs/FIXES.md`, sección 3).

> `Connection refused` en la pestaña 3 significa que el servidor de esa URL no
> está corriendo: revisa la pestaña 2 (o la 1 si usas `--url http://127.0.0.1:8089`).

### 3. Mensaje para los asistentes

> Trae un proyecto de Google Cloud con facturación activa. Antes de llegar,
> en Cloud Shell: clona `https://github.com/ricardochl/adk-a2a-marathon-agents`,
> corre `uv sync` (descarga bastante) y luego
> `uv run python scripts/check_env.py --skip-models`.

## Guion

| Min | Diapositivas | Qué hacer |
|---:|---|---|
| 0–8 | 1–4 | Qué construimos, qué es ADK y la arquitectura: una conexión local (AgentTool) y una remota (A2A). |
| 8–18 | 5–6 | Preparación en vivo (paso 1 de arriba). Todos corren `check_env.py`. Explica por qué fijamos versiones y la región `global`. |
| 18–35 | 7 | **Evaluador.** Leen el paso 4 del codelab. Abre `src/planner_agent/evaluator/config.py` y `tools.py`: los pesos, una métrica, el contrato JSON del juez y el respaldo heurístico. Corren `uv run pytest tests/test_evaluator_contract.py -q`. |
| 35–45 | 8 | **Simulator y ADK Skills.** Leen el paso 5. Abre `src/simulator_agent/agent/tools.py` y `skills/review-marathon-plan/SKILL.md`. |
| 45–58 | 9 | **Planner.** Leen el paso 6. Abre `src/planner_agent/agent/tools.py` (SkillToolset, AgentTool, RemoteA2aAgent) y `skills/route-planning/tools.py`. Corren `uv run pytest tests/test_deterministic.py -q -k route`. |
| 58–82 | 10–11 | **Probar.** Primero modo Solo (solo la pestaña del Planner, sin la variable), luego Equipo completo (las tres pestañas de arriba; mira la línea `Mode:`). Cada quien envía su pedido con su ciudad: `uv run python scripts/send_request.py "Plan a scenic marathon in San Pedro Sula for 10,000 runners, budget USD 1.5M"`. |
| 82–90 | 12 | Limpieza y preguntas. |

Para seguir el ritmo: **una comprobación por paso** y nadie avanza hasta que su
comando dé verde.

**Ejercicios opcionales.** Quien termine un paso antes que el resto puede hacer
el ejercicio de ese paso en [docs/EXERCISES.md](EXERCISES.md): 1 en el
Evaluador, 2 en el Simulator, 3 y 4 en el Planner y 5 después de la demo. No
los hagas en grupo si vas justo de tiempo; las soluciones están en la rama
`solutions` (`git diff main origin/solutions`).

## Si algo falla en vivo

| Síntoma | Qué hacer |
|---|---|
| `Connection refused` / `No A2A server at …` | El servidor no está corriendo: hay que levantarlo en otra pestaña (tabla de arriba) |
| `Address already in use` | Quedó un servidor viejo: `pkill -f local_server` y vuelve a levantarlo |
| La evaluación tarda minutos | Reinicia el Planner con `EVALUATOR_MODE=heuristic` y explica que el respaldo es parte del diseño |
| `Mode: SOLO` con el Simulator corriendo | Faltó `SIMULATOR_AGENT_RESOURCE_NAME=local:8089` al reiniciar el Planner |
| `404` de modelo | `GOOGLE_CLOUD_LOCATION=global`, o cambia `*_MODEL` a `gemini-2.5-flash` |
| `eval_method: heuristic_fallback` | Los jueces fallaron; `eval_error` dice por qué |
| `billingEnabled: false` | Vincular la cuenta de facturación: `gcloud billing accounts list` y `gcloud billing projects link <PROJECT_ID> --billing-account=<ACCOUNT_ID>` |
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

## Las etiquetas `step-XX`

No se usan durante el taller. Sirven para:

- **Mostrar qué agrega cada paso:** `git diff step-04 step-05 --stat` lista solo
  los archivos que aparecen en el paso 5. Proyectado, ayuda a explicar.
- **Rehacerlo en casa desde cero:** `git checkout step-03` y avanzar leyendo el
  codelab, comparando con la etiqueta siguiente si algo no funciona.
