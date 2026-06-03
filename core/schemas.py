"""
Esquemas de dominio (objetos de datos) compartidos por los agentes.

Se usan dataclasses de la librería estándar para que el núcleo no dependa
de paquetes externos. Estos objetos representan el "lenguaje común" con el
que los agentes se comunican entre sí.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Intent(str, Enum):
    """Intenciones que el Agente 1 puede reconocer en un mensaje del cliente."""
    GREETING = "saludo"
    BROWSE = "explorar_catalogo"
    RENT = "rentar"
    BUY = "comprar"
    CHECK_AVAILABILITY = "consultar_disponibilidad"
    RETURN = "devolver"
    SUPPORT = "soporte"
    GOODBYE = "despedida"
    UNKNOWN = "desconocido"


@dataclass
class RequestedItem:
    """Una película solicitada por el cliente dentro de un mensaje."""
    title_query: str                       # lo que el cliente escribió ("matrix")
    quantity: int = 1
    action: Optional[str] = None           # "rentar" | "comprar" | None
    matched: Optional[dict] = None         # fila del catálogo si se identificó

    @property
    def found(self) -> bool:
        return self.matched is not None

    @property
    def available(self) -> bool:
        """Hay stock suficiente para cubrir la cantidad pedida."""
        return bool(self.matched) and int(self.matched.get("stock", 0)) >= self.quantity


@dataclass
class TraceStep:
    """Un paso del razonamiento del agente (para explicabilidad)."""
    rule: str        # nombre de la regla / etapa aplicada
    detail: str      # explicación legible por humanos


@dataclass
class Interpretation:
    """
    Resultado producido por el Agente 1 a partir del mensaje del cliente.
    Es también el objeto que se entregará (handoff) al Agente 2.
    """
    raw_text: str
    intent: Intent = Intent.UNKNOWN
    items: list[RequestedItem] = field(default_factory=list)
    confidence: float = 0.0
    source: str = "rules"                   # "rules" | "llm" | "hybrid"
    trace: list[TraceStep] = field(default_factory=list)
    reply: str = ""                         # respuesta automática para el cliente

    def add_trace(self, rule: str, detail: str) -> None:
        """Registra un paso del razonamiento."""
        self.trace.append(TraceStep(rule=rule, detail=detail))

    def to_dict(self) -> dict:
        """Serializa la interpretación (útil para API/JSON)."""
        return {
            "raw_text": self.raw_text,
            "intent": self.intent.value,
            "confidence": round(self.confidence, 2),
            "source": self.source,
            "items": [
                {
                    "title_query": it.title_query,
                    "quantity": it.quantity,
                    "action": it.action,
                    "matched_title": it.matched["title"] if it.matched else None,
                    "available": it.available,
                }
                for it in self.items
            ],
            "trace": [{"rule": s.rule, "detail": s.detail} for s in self.trace],
            "reply": self.reply,
        }


@dataclass
class OrderLine:
    """Una línea del pedido: una película con su cantidad y precio."""
    title: str
    action: str                # "rentar" | "comprar"
    quantity: int
    unit_price: float
    line_total: float
    available: bool


@dataclass
class Order:
    """Pedido generado por el Agente 2 a partir de la interpretación del cliente."""
    customer_name: str
    lines: list[OrderLine] = field(default_factory=list)
    subtotal: float = 0.0
    discount_pct: float = 0.0
    discount_amount: float = 0.0
    total: float = 0.0
    restock: list = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)   # inferencias (reglas disparadas)
    status: str = "propuesto"                            # propuesto | confirmado | sin_items
    order_id: Optional[int] = None                       # se asigna al guardar en BD (Día 4)

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "customer_name": self.customer_name,
            "status": self.status,
            "lines": [
                {
                    "title": ln.title, "action": ln.action, "quantity": ln.quantity,
                    "unit_price": ln.unit_price, "line_total": ln.line_total,
                    "available": ln.available,
                }
                for ln in self.lines
            ],
            "subtotal": self.subtotal,
            "discount_pct": self.discount_pct,
            "discount_amount": self.discount_amount,
            "total": self.total,
            "restock": self.restock,
            "reasoning": self.reasoning,
        }
