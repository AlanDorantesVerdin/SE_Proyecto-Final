"""
Agente 2 — Generador de Pedido.

Responsabilidades (según los requisitos del proyecto):
  • Procesar la información recibida del Agente 1.
  • Validar la información (existencia y stock contra el catálogo).
  • Realizar inferencias (motor de reglas: descuentos, reabastecimiento).
  • Generar el pedido (líneas, subtotal, descuento, total).

Conserva el razonamiento (reglas disparadas) para la EXPLICABILIDAD que mostrará
el Agente 3. La persistencia en base de datos se añade en el Día 4.
"""
from __future__ import annotations

from core.business_rules import build_order_rules, make_order_facts
from core.inference_engine import InferenceEngine
from core.schemas import Intent, Interpretation, Order, OrderLine
from database.repository import (
    count_overdue_rentals,
    ensure_customer,
    get_customer_by_phone,
    persist_order,
)


class OrderGeneratorAgent:
    """Convierte la interpretación del cliente en un pedido con inferencias."""

    name = "Agente 2 — Generador de Pedido"

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path
        self.engine = InferenceEngine(build_order_rules())

    def process(self, interpretation: Interpretation,
                customer_phone: str | None = None) -> Order:
        """Genera el pedido a partir de la interpretación del Agente 1."""
        customer_row = get_customer_by_phone(customer_phone, self.db_path)
        customer = dict(customer_row) if customer_row else None
        customer_name = customer["name"] if customer else "Cliente no registrado"

        items = self._items_from_interpretation(interpretation)
        if not items:
            return Order(
                customer_name=customer_name,
                status="sin_items",
                reasoning=["No se identificaron películas del catálogo para el pedido."],
            )

        # Motor de inferencia: aplica las reglas de negocio sobre el pedido.
        facts = make_order_facts(customer, items)
        if customer:
            facts["overdue_count"] = count_overdue_rentals(customer["id"], self.db_path)
        result = self.engine.run(facts)

        lines = [
            OrderLine(
                title=it["title"], action=it["action"], quantity=it["quantity"],
                unit_price=it["unit_price"], line_total=it["line_total"],
                available=it["available"],
            )
            for it in facts["items"]
        ]
        return Order(
            customer_name=customer_name,
            lines=lines,
            subtotal=facts["subtotal"],
            discount_pct=facts["discount_pct"],
            discount_amount=facts.get("discount_amount", 0.0),
            total=facts.get("total", 0.0),
            restock=facts["restock"],
            reasoning=result.reasoning,
            status="propuesto",
        )

    def confirm(self, order: Order, customer_phone: str | None = None) -> Order:
        """
        Persiste el pedido en la base de datos (todo o nada): guarda el pedido y
        sus líneas, descuenta el stock, registra las rentas con su fecha de
        vencimiento y anota las sugerencias de reabastecimiento.
        """
        if order.status == "sin_items" or not order.lines:
            return order

        customer_id = ensure_customer(customer_phone, order.customer_name, self.db_path)

        acciones = {ln.action for ln in order.lines if ln.available}
        if acciones == {"rentar"}:
            tipo = "renta"
        elif acciones == {"comprar"}:
            tipo = "compra"
        elif acciones:
            tipo = "mixto"
        else:
            tipo = "compra"

        order.order_id = persist_order(
            customer_id=customer_id, tipo=tipo, order=order, db_path=self.db_path
        )
        order.status = "confirmado"
        return order

    def _items_from_interpretation(self, interp: Interpretation) -> list[dict]:
        """Toma solo los ítems identificados en el catálogo y normaliza la acción."""
        default_action = "rentar" if interp.intent == Intent.RENT else "comprar"
        items = []
        for it in interp.items:
            if not it.found:
                continue
            movie = it.matched
            items.append({
                "title": movie["title"],
                "quantity": it.quantity,
                "action": it.action or default_action,
                "stock": movie["stock"],
                "price_rent": movie["price_rent"],
                "price_buy": movie["price_buy"],
            })
        return items
