"""
Demostración de la persistencia del Agente 2 (Día 4).

Ejecuta:
    python run_persist.py

Genera un pedido, lo CONFIRMA (lo guarda en la base de datos) y verifica:
  • el pedido y sus líneas quedaron almacenados,
  • el stock se descontó,
  • se creó la renta con fecha de vencimiento,
  • se registró la sugerencia de reabastecimiento del título agotado,
  • el conteo de rentas del cliente se actualizó.
"""
from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from agents.agent_orders import OrderGeneratorAgent
from core.console import enable_utf8
from core.schemas import Intent, Interpretation, RequestedItem
from database.repository import (
    get_customer_by_phone,
    get_movie_by_title,
    get_order,
    list_rentals,
    list_restock,
)
from database.seed import seed

enable_utf8()

FRECUENTE = "+5216561234567"   # Alan (cliente frecuente, en el seed)


def _item(title, qty, action, stock, rent, buy) -> RequestedItem:
    return RequestedItem(
        title_query=title, quantity=qty, action=action,
        matched={"title": title, "stock": stock, "price_rent": rent, "price_buy": buy},
    )


def main() -> None:
    seed()  # estado limpio y conocido (también limpia pedidos/rentas previos)
    agent2 = OrderGeneratorAgent()

    matrix_antes = get_movie_by_title("The Matrix")["stock"]
    rentas_antes = get_customer_by_phone(FRECUENTE)["rentals_count"]
    print(f"ANTES  ->  Stock 'The Matrix': {matrix_antes}  |  "
          f"rentas del cliente: {rentas_antes}\n")

    # Pedido: rentar 2 Matrix (disponible) + 1 Forrest Gump (agotado)
    interp = Interpretation(raw_text="rentar 2 matrix y forrest gump", intent=Intent.RENT)
    interp.items = [
        _item("The Matrix", 2, "rentar", matrix_antes, 39, 149),
        _item("Forrest Gump", 1, "rentar", 0, 35, 129),
    ]

    order = agent2.process(interp, customer_phone=FRECUENTE)
    order = agent2.confirm(order, customer_phone=FRECUENTE)   # <-- PERSISTE en la BD

    print(f"Pedido #{order.order_id} guardado | estado: {order.status} | "
          f"total ${order.total:.0f}\n")

    # ---- Verificación contra la base de datos ----
    matrix_despues = get_movie_by_title("The Matrix")["stock"]
    db_order, db_items = get_order(order.order_id)
    rentals = list_rentals()
    restock = list_restock()
    rentas_despues = get_customer_by_phone(FRECUENTE)["rentals_count"]

    print("Pedido en la BD:")
    for it in db_items:
        print(f"   - {it['quantity']}x {it['title']} @ ${it['unit_price']:.0f}")
    print(f"\nStock 'The Matrix': {matrix_antes} -> {matrix_despues}")
    print("Rentas registradas (con vencimiento):")
    for r in rentals:
        print(f"   - {r['title']} | vence {r['due_date']} | estado {r['status']}")
    print("Sugerencias de reabastecimiento:")
    for r in restock:
        print(f"   - {r['title']} (faltan {r['suggested_qty']})")
    print(f"\nRentas del cliente: {rentas_antes} -> {rentas_despues}")

    # ---- Validaciones (prueba de humo) ----
    assert db_order is not None, "El pedido debe existir en la BD"
    assert matrix_despues == matrix_antes - 2, "El stock debe descontarse"
    assert any(r["title"] == "The Matrix" for r in rentals), "Debe crearse la renta"
    assert any(r["title"] == "Forrest Gump" for r in restock), "Debe registrarse reabastecimiento"
    assert rentas_despues == rentas_antes + 2, "Debe incrementar el conteo de rentas"

    print("\n✅ Persistencia verificada: pedido, stock, rentas y reabastecimiento.")


if __name__ == "__main__":
    main()
