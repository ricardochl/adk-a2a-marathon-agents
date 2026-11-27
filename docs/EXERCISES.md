# Ejercicios opcionales

Para quien termina antes o quiere practicar después del taller. Ninguno es
necesario para la demo final: el código de `main` ya funciona completo.

Todos siguen el mismo hilo: **adaptar el sistema a una maratón en clima
caluroso, como San Pedro Sula.** Se pueden hacer en cualquier orden, aunque el
5 tiene más sentido después del 2.

| # | Paso del taller | Ejercicio | Tiempo | Se comprueba con |
|---|---|---|---|---|
| 1 | Evaluador | Darle más peso a la seguridad | 5 min | `uv run pytest -m exercise -k ex1` |
| 2 | Simulator | Exigir un protocolo de calor | 10 min | `uv run pytest -m exercise -k ex2` |
| 3 | Planner | Escribir una herramienta nueva | 15 min | `uv run pytest -m exercise -k ex3` |
| 4 | Planner | Agregar tu ciudad | 5 min | `uv run python scripts/try_route.py "Tu ciudad"` |
| 5 | Planner | Enseñarle al Planner el protocolo de calor | 10 min | `uv run pytest -m exercise -k ex5` y un pedido real |

Los tests de ejercicios fallan hasta que resuelves cada uno; por eso no corren
con el `uv run pytest` normal.

**Si te trabas:** las soluciones están en la rama `solutions`. Para ver la de
un archivo sin perder tu trabajo:

```bash
git diff main origin/solutions -- src/simulator_agent/agent/tools.py
```

**Para deshacer un ejercicio y volver a `main`:**

```bash
git checkout -- <archivo>     # un archivo
git checkout -- .             # todos los cambios
```

---

## Ejercicio 1 · Darle más peso a la seguridad

**Qué aprendes:** las reglas del juez son código, y los tests las protegen.

En una maratón con calor, un problema de seguridad (golpes de calor,
deshidratación) es más grave que en clima templado. Queremos que el Evaluador
lo refleje en la calificación.

**Archivo:** `src/planner_agent/evaluator/config.py`

**Qué hacer:** en `CRITERION_WEIGHTS`, sube `safety_compliance` de `0.20` a
`0.25` y baja `community_impact` de `0.15` a `0.10`.

**Comprueba:**

```bash
uv run pytest -m exercise -k ex1     # el ejercicio
uv run pytest                         # el resto sigue en verde
```

**Para pensar:** cambia solo un peso, sin compensar el otro, y corre
`uv run pytest`. ¿Qué test falla y por qué? Los pesos deben sumar 1.0: si no,
el puntaje final deja de estar en la escala de 0 a 100.

---

## Ejercicio 2 · Exigir un protocolo de calor

**Qué aprendes:** no todo es IA. El Simulator revisa con reglas fijas de
Python, y agregar una regla es agregar una línea.

**Archivo:** `src/simulator_agent/agent/tools.py`

**Qué hacer:** en el diccionario `checklist` de `check_plan_readiness`, agrega
un noveno punto, `"heat_protocol"`, que sea verdadero si el plan menciona
alguna de estas palabras: `"heat protocol"`, `"heat index"`, `"cooling"` o
`"calor"`. Después agrégalo al conjunto `BLOCKING_CHECKS` (arriba del
archivo) para que, si falta, bloquee el plan.

> **Pista:** copia la forma de la línea `"medical_tents"`, que ya revisa una
> lista de palabras con `any(...)`.

**Comprueba:**

```bash
uv run pytest -m exercise -k ex2
```

**Pruébalo de verdad:** levanta el Simulator y mándale un plan sin protocolo de
calor. Debe bloquearlo y nombrar el punto que falta:

```bash
# pestaña 1
uv run python -m src.simulator_agent.runtime.local_server
# pestaña 2: el plan de ejemplo sin la línea del protocolo de calor
grep -v "Heat protocol" examples/sample_plan.md > /tmp/sin_calor.md
uv run python scripts/send_request.py --url http://127.0.0.1:8089 --file /tmp/sin_calor.md
```

Si quieres que el agente lo explique mejor, agrega la regla también en
`src/simulator_agent/skills/review-marathon-plan/references/readiness_checklist.md`.

---

## Ejercicio 3 · Escribir una herramienta nueva

**Qué aprendes:** lo central de ADK. Una función de Python, con una buena
docstring, se convierte en una herramienta que el agente decide cuándo usar.

**Archivo:** `src/planner_agent/agent/tools.py`

**Qué hacer:**

1. Escribe una función `estimate_budget(participants: int, cost_per_runner_usd: float = 130.0) -> dict`
   que devuelva un diccionario con estas claves:

   | Clave | Cálculo |
   |---|---|
   | `participants` | el número de corredores recibido |
   | `cost_per_runner_usd` | el costo por corredor recibido |
   | `total_cost_usd` | `participants × cost_per_runner_usd` |
   | `suggested_registration_fee_usd` | 60% del costo por corredor (la inscripción cubre el 60%) |
   | `sponsorship_needed_usd` | lo que falta: costo total menos lo que pagan las inscripciones |

2. Escríbele una docstring en inglés que diga qué hace y qué significa cada
   argumento. **El modelo la lee para decidir cuándo usar la herramienta**:
   una docstring vaga hace que el agente no la use o la use mal.

3. En `get_tools()`, junto a la línea que agrega `plan_marathon_route`, agrega
   la tuya:

   ```python
   tools.append(FunctionTool(func=estimate_budget))
   ```

**Comprueba:**

```bash
uv run pytest -m exercise -k ex3
```

Luego levanta el Planner: en la línea `Tools:` debe aparecer `estimate_budget`.
Envía un pedido que hable de presupuesto y revisa en la pestaña del Planner si
el agente la llamó.

**Para pensar:** ¿por qué esta cuenta es mejor como herramienta que dejársela
al modelo? Los modelos se equivocan en aritmética; una función de Python, no.

---

## Ejercicio 4 · Agregar tu ciudad

**Qué aprendes:** cómo la herramienta de rutas decide dónde dibujar la
maratón, y por qué avisa cuando no conoce una ciudad.

**Archivo:** `src/planner_agent/skills/route-planning/tools.py`

**Primero mira qué pasa hoy:**

```bash
uv run python scripts/try_route.py "La Ceiba"
```

Dice que la ciudad no está en la lista y que la ruta usa un centro de
reemplazo.

**Qué hacer:** agrega tu ciudad a `CITY_CENTERS`, en minúsculas y sin tildes,
con su latitud y longitud. Para obtenerlas, en Google Maps haz clic derecho
sobre el centro de la ciudad: el primer renglón del menú son las coordenadas.

```python
"la ceiba": (15.78, -86.79),   # ejemplo aproximado
```

**Comprueba:**

```bash
uv run python scripts/try_route.py "La Ceiba, Honduras"
uv run pytest
```

Debe decir `known city` y la distancia de 42.195 km. El script guarda la ruta
en `route.geojson`; descárgala de Cloud Shell y ábrela en
[geojson.io](https://geojson.io) para verla en un mapa.

**Opcional:** agrega un apodo en `CITY_ALIASES`, como ya existe `"sps"` para
San Pedro Sula.

---

## Ejercicio 5 · Enseñarle al Planner el protocolo de calor

**Qué aprendes:** la instrucción cambia el comportamiento del agente sin tocar
código. Y si hiciste el ejercicio 2, cierras el ciclo: el inspector ahora exige
algo que el Planner todavía no sabe incluir.

**Archivo:** `src/planner_agent/agent/planner-instruction.md`

**Qué hacer:** en la sección `# Core Requirements`, agrega una regla en inglés,
como el resto del archivo, que pida incluir un **heat protocol** (protocolo de
calor) en las ciudades calurosas: hora de salida temprana, puestos de
hidratación más frecuentes, zonas de enfriamiento y un umbral de índice de
calor para suspender la carrera.

**Comprueba:**

```bash
uv run pytest -m exercise -k ex5
```

**Pruébalo de verdad:** con el ejercicio 2 hecho, levanta el Simulator y el
Planner en modo Equipo completo y envía el pedido de ejemplo de San Pedro Sula.
Compara con lo que pasaba antes de los ejercicios:

- ¿El plan incluye ahora un protocolo de calor?
- ¿El Simulator lo aprueba?
- ¿Cambió el puntaje del Evaluador con los pesos del ejercicio 1?
