# Simulation Readiness Checklist

> Added for the workshop repo (the codelab creates this `references/` folder but leaves it empty).

| Category  | Item                | Counts as present when the plan mentions…                 | Blocking? |
|-----------|---------------------|------------------------------------------------------------|-----------|
| Route     | Distance            | A number in miles/mi or km/kilometers                      | Yes       |
| Route     | Start / finish      | "start line", "finish line", "start/finish", "starting area" | Yes     |
| Logistics | Water stations      | "water station"                                            | Yes       |
| Logistics | Medical             | "medical tent", "first aid", "medical station"             | Yes       |
| Logistics | Timing              | "timing", "chip", "tracking"                               | Yes       |
| Safety    | Emergency access    | "emergency", "ambulance", "evacuation"                     | Yes       |
| Finance   | Budget              | "budget", "cost", "revenue", "expense"                     | No        |
| Ops       | Timeline            | "schedule", "timeline", "race day", "setup"                | No        |
| Safety    | Heat protocol       | "heat protocol", "heat index", "cooling", "calor"          | Yes       |

## Decision rules

- `approved = true` only when every **blocking** item is present.
- `route_feasibility`: `feasible` if distance + start/finish present, `marginal` if only one, otherwise `infeasible`.
- `logistics_readiness`: `ready` (3/3), `partial` (1–2/3), `not_ready` (0/3).
- `safety_clearance`: `cleared` if emergency access present, otherwise `blocked`.
- Non-blocking gaps go to `recommendations`, never to `blockers`.
