# Simulation Readiness Checklist

> Added for the workshop repo (the codelab creates this `references/` folder but leaves it empty).

| Category  | Item                | Counts as present when the plan mentions… (English or Spanish) | Blocking? |
|-----------|---------------------|------------------------------------------------------------|-----------|
| Route     | Distance            | A number in miles/mi or km/kilómetros                      | Yes       |
| Route     | Start / finish      | "start line", "finish line", "línea de salida", "línea de meta" | Yes     |
| Logistics | Water stations      | "water station", "estación de agua", "hidratación"                                            | Yes       |
| Logistics | Medical             | "medical tent", "first aid", "carpa médica", "primeros auxilios"             | Yes       |
| Logistics | Timing              | "timing", "chip", "tracking", "cronometraje"                               | Yes       |
| Safety    | Emergency access    | "emergency", "ambulance", "emergencia", "ambulancia"                     | Yes       |
| Finance   | Budget              | "budget", "cost", "presupuesto", "costo"                     | No        |
| Ops       | Timeline            | "schedule", "timeline", "cronograma", "horario"                | No        |
| Safety    | Heat protocol       | "heat protocol", "heat index", "cooling", "calor"          | Yes       |

## Decision rules

- `approved = true` only when every **blocking** item is present.
- `route_feasibility`: `feasible` if distance + start/finish present, `marginal` if only one, otherwise `infeasible`.
- `logistics_readiness`: `ready` (3/3), `partial` (1–2/3), `not_ready` (0/3).
- `safety_clearance`: `cleared` if emergency access present, otherwise `blocked`.
- Non-blocking gaps go to `recommendations`, never to `blockers`.
