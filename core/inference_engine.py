"""
Motor de inferencia (encadenamiento hacia adelante / forward chaining).

Es el componente central del SISTEMA EXPERTO: aplica una base de reglas IF/THEN
sobre un conjunto de hechos (memoria de trabajo) y deriva conclusiones,
registrando QUÉ regla se disparó y POR QUÉ (explicabilidad).

Es genérico: no sabe nada de películas. Las reglas concretas del negocio viven
en `core/business_rules.py`. Así el motor podría reutilizarse en otro dominio.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Rule:
    """Una regla IF/THEN de la base de conocimiento."""
    name: str
    description: str                    # "SI ... ENTONCES ..." legible por humanos
    condition: Callable[[dict], bool]  # parte IF: predicado sobre los hechos
    action: Callable[[dict], str]      # parte THEN: modifica los hechos y devuelve la explicación
    priority: int = 0                  # mayor prioridad = se evalúa primero


@dataclass
class FiredRule:
    """Registro de una regla que se disparó (para la traza de razonamiento)."""
    name: str
    description: str
    explanation: str


@dataclass
class InferenceResult:
    """Resultado de una corrida del motor."""
    facts: dict
    fired: list[FiredRule] = field(default_factory=list)

    @property
    def reasoning(self) -> list[str]:
        """Explicaciones en orden, para mostrar el razonamiento al usuario."""
        return [f.explanation for f in self.fired]


class InferenceEngine:
    """Encadenamiento hacia adelante con reglas priorizadas."""

    def __init__(self, rules: list[Rule]):
        self.rules = list(rules)

    def run(self, facts: dict, max_passes: int = 10) -> InferenceResult:
        """
        Aplica las reglas sobre `facts` hasta que ninguna nueva se dispare.

        - Cada regla se dispara como máximo una vez.
        - Las reglas se evalúan por prioridad (mayor primero).
        - Si una regla falla por datos faltantes, se omite sin tumbar el motor.
        - El encadenamiento permite que el efecto de una regla active otra
          (p. ej. los descuentos disparan luego la regla de 'tope de descuento').
        """
        fired: list[FiredRule] = []
        fired_names: set[str] = set()
        ordered = sorted(self.rules, key=lambda r: -r.priority)

        for _ in range(max_passes):
            progressed = False
            for rule in ordered:
                if rule.name in fired_names:
                    continue
                try:
                    if rule.condition(facts):
                        explanation = rule.action(facts)
                        fired.append(FiredRule(rule.name, rule.description, explanation))
                        fired_names.add(rule.name)
                        progressed = True
                except Exception:  # noqa: BLE001 — una regla mal alimentada no debe romper todo
                    continue
            if not progressed:
                break

        return InferenceResult(facts=facts, fired=fired)
