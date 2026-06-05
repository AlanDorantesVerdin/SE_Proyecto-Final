"""
Demostración del Agente 3 (Supervisor/Explicador) y del flujo completo (Día 5).

Ejecuta:
    python run_supervisor.py

Muestra el flujo de los TRES agentes:
    Agente 1 (interpreta) -> Agente 2 (genera pedido) -> Agente 3 (explica y valida)
"""
from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from agents.agent_customer import CustomerServiceAgent
from agents.agent_orders import OrderGeneratorAgent
from agents.agent_supervisor import SupervisorAgent
from core.console import enable_utf8
from core.schemas import Intent, Interpretation, RequestedItem
from database.repository import count_movies
from database.seed import seed

enable_utf8()

FRECUENTE = "+5216561234567"   # Alan (cliente frecuente, en el seed)


def _item(title, qty, action, stock, rent, buy) -> RequestedItem:
    return RequestedItem(
        title_query=title, quantity=qty, action=action,
        matched={"title": title, "stock": stock, "price_rent": rent, "price_buy": buy},
    )


def main() -> None:
    if count_movies() == 0:
        seed()
    agent1 = CustomerServiceAgent()
    agent2 = OrderGeneratorAgent()
    agent3 = SupervisorAgent()

    print("=" * 64)
    print("PARTE 1 — Agente 3 sobre un pedido con varios descuentos")
    print("=" * 64)
    interp = Interpretation(raw_text="comprar 2 el padrino y 3 matrix", intent=Intent.BUY)
    interp.items = [
        _item("El Padrino", 2, "comprar", 3, 49, 199),
        _item("The Matrix", 3, "comprar", 8, 39, 149),
    ]
    order = agent2.process(interp, customer_phone=FRECUENTE)
    report = agent3.review(order)
    print(report.message + "\n")
    assert "Total" in report.message
    assert report.decisions, "El reporte debe explicar inferencias"
    assert "SÍ" in report.validation_request

    print("=" * 64)
    print("PARTE 2 — Agente 3 con un título agotado (requiere atención)")
    print("=" * 64)
    interp2 = Interpretation(raw_text="rentar forrest gump", intent=Intent.RENT)
    interp2.items = [_item("Forrest Gump", 2, "rentar", 0, 35, 129)]
    order2 = agent2.process(interp2, customer_phone=FRECUENTE)
    report2 = agent3.review(order2)
    print(report2.message + "\n")
    assert report2.requires_attention, "Debe marcar atención por reabastecimiento"

    print("=" * 64)
    print("PARTE 3 — FLUJO COMPLETO 1 -> 2 -> 3 (mensaje real)")
    print("=" * 64)
    msg = "Hola, quiero comprar Shrek y rentar El Padrino"
    print(f"🧑 Cliente: {msg}\n")
    interpretation = agent1.handle(msg, customer_phone=FRECUENTE)
    order3 = agent2.process(interpretation, customer_phone=FRECUENTE)
    report3 = agent3.review(order3)
    print(report3.message + "\n")

    print("✅ Agente 3 verificado: resumen, explicación de inferencias y validación.")


if __name__ == "__main__":
    main()
