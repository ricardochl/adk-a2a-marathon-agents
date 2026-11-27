"""Tools for the Simulation Controller Agent."""

import re
from typing import Any

# Missing any of these blocks the plan. The rest only produce recommendations.
BLOCKING_CHECKS = {
    "distance_specified", "water_stations", "medical_tents",
    "timing_system", "start_finish", "emergency_access",
}


async def check_plan_readiness(plan_text: str) -> dict[str, Any]:
    """Check a marathon plan for simulation readiness.

    Performs deterministic checks on the plan text to identify
    missing elements and assess completeness. The approval decision is made
    here, in code: `approved`, `blockers` and `recommendations` are final.
    """
    plan_lower = plan_text.lower()

    # Keywords in English and Spanish: the Planner writes its plans in Spanish.
    checklist = {
        "distance_specified": bool(
            re.search(r'(\d+(?:\.\d+)?)\s*(?:miles?|mi|kilometers?|kil[oó]metros?|km)\b', plan_lower)
        ),
        "water_stations": any(kw in plan_lower for kw in [
            "water station", "estación de agua", "estaciones de agua", "hidratación"]),
        "medical_tents": any(kw in plan_lower for kw in [
            "medical tent", "first aid", "medical station",
            "carpa médica", "carpas médicas", "primeros auxilios", "puesto médico", "puestos médicos",
            "atención médica", "punto médico", "puntos médicos", "clínica"]),
        "timing_system": any(kw in plan_lower for kw in ["timing", "chip", "tracking", "cronometraje", "rfid"]),
        "start_finish": any(kw in plan_lower for kw in [
            "start line", "finish line", "start/finish", "starting area",
            "línea de salida", "línea de meta", "salida y meta", "salida/meta", "zona de salida"]),
        "emergency_access": any(kw in plan_lower for kw in [
            "emergency", "ambulance", "evacuation", "emergencia", "ambulancia", "evacuación"]),
        "budget_included": any(kw in plan_lower for kw in [
            "budget", "cost", "revenue", "expense", "presupuesto", "costo", "ingreso", "gasto"]),
        "timeline_included": any(kw in plan_lower for kw in [
            "schedule", "timeline", "race day", "setup", "cronograma", "horario", "día de la carrera", "montaje"]),
        # Exercise 2: hot-climate races need a heat protocol.
        "heat_protocol": any(kw in plan_lower for kw in ["heat protocol", "heat index", "cooling", "calor"]),
    }

    passed = sum(checklist.values())
    total = len(checklist)
    missing = [k for k, v in checklist.items() if not v]
    blockers = [k for k in missing if k in BLOCKING_CHECKS]

    return {
        "approved": not blockers,
        "blockers": blockers,
        "recommendations": [k for k in missing if k not in BLOCKING_CHECKS],
        "checklist": checklist,
        "missing_elements": missing,
        "readiness_score": round(passed / total, 2),
        "passed_checks": passed,
        "total_checks": total,
    }


def get_tools() -> list:
    return [check_plan_readiness]
