"""
Demostración del Agente 2 (Generador de Pedido) — Día 3.

Ejecuta:
    python run_orders.py

Muestra dos cosas:
  1. Pruebas deterministas del Agente 2 (con interpretaciones simuladas + assert).
  2. El flujo completo Agente 1 -> Agente 2 con mensajes reales.
"""
from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from agents.agent_customer import CustomerServiceAgent
from agents.agent_orders import OrderGeneratorAgent
from core.console import enable_utf8
from core.schemas import Intent, Interpretation, RequestedItem
from database.repository import count_movies
from database.seed import seed

enable_utf8()

FRECUENTE = "+5216561234567"   # Alan (cliente frecuente, en el seed)
NORMAL = "+5216567654321"      # María (no frecuente)


def print_order(order) -> None:
    print(f"  Cliente: {order.customer_name} | Estado: {order.status}")
    for ln in order.lines:
        marca = "✓" if ln.available else "✗ agotado"
        print(f"   - {ln.quantity}x {ln.title} [{ln.action}] "
              f"${ln.unit_price:.0f} c/u = ${ln.line_total:.0f}  {marca}")
    print(f"  Subtotal ${order.subtotal:.0f} | Descuento {order.discount_pct}% "
          f"(${order.discount_amount:.0f}) | TOTAL ${order.total:.0f}")
    if order.restock:
        print(f"  Reabastecer: {order.restock}")
    print("  Razonamiento (inferencias):")
    for r in order.reasoning:
        print(f"    • {r}")
    print()


def _item(title, qty, action, stock, rent, buy) -> RequestedItem:
    """Crea un ítem ya 'identificado' en el catálogo (simula la salida del Agente 1)."""
    return RequestedItem(
        title_query=title, quantity=qty, action=action,
        matched={"title": title, "stock": stock, "price_rent": rent, "price_buy": buy},
    )


def main() -> None:
    if count_movies() == 0:
        seed()
    agent2 = OrderGeneratorAgent()

    print("=" * 66)
    print("PARTE 1 — Pruebas deterministas del Agente 2")
    print("=" * 66)

    # Escenario A: cliente frecuente, pedido grande -> varios descuentos + tope
    interp = Interpretation(raw_text="comprar 3 matrix y 2 el padrino", intent=Intent.BUY)
    interp.items = [
        _item("The Matrix", 3, "comprar", 8, 39, 149),
        _item("El Padrino", 2, "comprar", 3, 49, 199),
    ]
    print("Escenario A: frecuente, 3 Matrix + 2 El Padrino")
    order_a = agent2.process(interp, customer_phone=FRECUENTE)
    print_order(order_a)
    assert order_a.discount_pct == 25
    assert order_a.total == round(845 * 0.75, 2)

    # Escenario B: película agotada -> reabastecimiento
    interp = Interpretation(raw_text="rentar forrest gump", intent=Intent.RENT)
    interp.items = [_item("Forrest Gump", 2, "rentar", 0, 35, 129)]
    print("Escenario B: cliente normal, Forrest Gump (agotado)")
    order_b = agent2.process(interp, customer_phone=NORMAL)
    print_order(order_b)
    assert order_b.restock, "Debe sugerir reabastecimiento"

    print("=" * 66)
    print("PARTE 2 — Flujo completo Agente 1 -> Agente 2 (mensajes reales)")
    print("=" * 66)
    agent1 = CustomerServiceAgent()
    for msg in ["Hola, quiero comprar Shrek y The Matrix", "quiero rentar el padrino"]:
        print(f"🧑 Cliente: {msg}")
        interpretation = agent1.handle(msg, customer_phone=FRECUENTE)
        order = agent2.process(interpretation, customer_phone=FRECUENTE)
        print_order(order)

    print("✅ Agente 2 verificado: validación, inferencias y total correctos.")


if __name__ == "__main__":
    main()
