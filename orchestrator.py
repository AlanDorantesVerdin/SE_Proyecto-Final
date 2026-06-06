"""
Orquestador del flujo conversacional de los tres agentes.

Coordina:
    Agente 1 (interpretar) -> Agente 2 (generar pedido)
    -> Agente 3 (explicar y pedir validación) -> confirmación -> guardar en BD.

Mantiene un estado de conversación por cliente (teléfono): cuando hay un pedido
pendiente de confirmación, el siguiente mensaje se interpreta como SÍ/NO.

Nota: el estado vive en memoria del proceso (suficiente para la demo local con
un solo worker). En producción multiproceso convendría usar una BD o Redis.
"""
from __future__ import annotations

import unicodedata

from agents.agent_customer import CustomerServiceAgent
from agents.agent_orders import OrderGeneratorAgent
from agents.agent_supervisor import SupervisorAgent
from core.llm_client import LLMClient
from core.schemas import Intent, Order

# Palabras para detectar confirmación / cancelación.
_SI = {"si", "claro", "confirmo", "confirmar", "dale", "ok", "okay",
       "va", "vale", "afirmativo", "sip", "simon"}
_NO = {"no", "cancela", "cancelar", "nel", "negativo", "olvidalo"}

# Solo estas intenciones generan una propuesta de pedido.
_ORDER_INTENTS = {Intent.RENT, Intent.BUY}


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


class Orchestrator:
    """Coordina los tres agentes y la conversación con cada cliente."""

    def __init__(self, db_path: str | None = None, llm: LLMClient | None = None):
        self.agent1 = CustomerServiceAgent(llm=llm, db_path=db_path)
        self.agent2 = OrderGeneratorAgent(db_path=db_path)
        self.agent3 = SupervisorAgent()
        self._pending: dict[str, Order] = {}   # teléfono -> pedido en espera de confirmación

    def handle_message(self, text: str, phone: str | None = None) -> str:
        """Punto de entrada único: recibe un mensaje y devuelve la respuesta."""
        key = phone or "anon"
        if key in self._pending:
            return self._handle_confirmation(text, key)
        return self._handle_new_request(text, phone, key)

    def _handle_new_request(self, text: str, phone: str | None, key: str) -> str:
        interp = self.agent1.handle(text, customer_phone=phone)

        # Saludo, catálogo, soporte, etc.: responde el Agente 1, sin generar pedido.
        if interp.intent not in _ORDER_INTENTS or not interp.items:
            return interp.reply

        order = self.agent2.process(interp, customer_phone=phone)
        report = self.agent3.review(order)

        # Solo dejamos un pedido pendiente si hay algo disponible que confirmar.
        if any(ln.available for ln in order.lines):
            self._pending[key] = order
        return report.message

    def _handle_confirmation(self, text: str, key: str) -> str:
        order = self._pending[key]
        decision = self._yes_no(text)

        if decision == "si":
            phone = None if key == "anon" else key
            confirmed = self.agent2.confirm(order, customer_phone=phone)
            del self._pending[key]
            return self._confirmation_message(confirmed)

        if decision == "no":
            del self._pending[key]
            return "Tu pedido fue cancelado. ¿Puedo ayudarte con algo más? 🎬"

        return ("Tienes un pedido pendiente. Responde *SÍ* para confirmarlo "
                "o *NO* para cancelarlo.")

    @staticmethod
    def _yes_no(text: str) -> str | None:
        norm = _normalize(text)
        palabras = set(norm.split())
        if palabras & _SI:
            return "si"
        if palabras & _NO:
            return "no"
        return None

    @staticmethod
    def _confirmation_message(order: Order) -> str:
        lineas = ", ".join(
            f"{ln.quantity}x {ln.title}" for ln in order.lines if ln.available
        )
        return (f"✅ ¡Pedido #{order.order_id} confirmado!\n"
                f"{lineas}\n"
                f"Total: ${order.total:.0f}. "
                "¡Gracias por tu preferencia en *CineFísico*! 🎬")
