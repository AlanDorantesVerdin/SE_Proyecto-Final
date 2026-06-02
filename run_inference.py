"""
Demostración del motor de inferencia y las reglas de negocio (Día 2).

Ejecuta:
    python run_inference.py

Muestra varios escenarios de pedido y CÓMO razona el sistema experto:
qué reglas IF/THEN se disparan y por qué. Incluye validaciones (assert) que
funcionan como prueba de humo del motor.
"""
from __future__ import annotations

from core.business_rules import build_order_rules, make_order_facts
from core.console import enable_utf8
from core.inference_engine import InferenceEngine

enable_utf8()


def evaluar(titulo: str, customer: dict | None, items: list[dict]) -> dict:
    """Construye los hechos, corre el motor y muestra el razonamiento."""
    facts = make_order_facts(customer, items)
    result = InferenceEngine(build_order_rules()).run(facts)

    print("=" * 66)
    print(f"ESCENARIO: {titulo}")
    print("-" * 66)
    cliente = customer["name"] if customer else "No registrado"
    print(f"Cliente: {cliente} | Subtotal: ${facts['subtotal']:.0f} | "
          f"Unidades: {facts['units_total']}")
    print("\nRazonamiento (reglas IF/THEN disparadas):")
    for fr in result.fired:
        print(f"  • [{fr.name}] {fr.description}")
        print(f"      → {fr.explanation}")
    print(f"\nResultado: descuento {facts.get('discount_pct', 0)}% | "
          f"TOTAL ${facts.get('total', 0):.0f}")
    if facts["restock"]:
        print(f"Sugerencia de reabastecimiento: {facts['restock']}")
    print("=" * 66 + "\n")
    return facts


def main() -> None:
    # Catálogo de prueba (precio y stock)
    matrix = {"title": "The Matrix", "stock": 8, "price_rent": 39, "price_buy": 149}
    padrino = {"title": "El Padrino", "stock": 3, "price_rent": 49, "price_buy": 199}
    forrest = {"title": "Forrest Gump", "stock": 0, "price_rent": 35, "price_buy": 129}

    frecuente = {"name": "Alan Dorantes", "is_frequent": True, "rentals_count": 7}
    normal = {"name": "María López", "is_frequent": False, "rentals_count": 1}

    # 1) Cliente frecuente, compra simple
    f1 = evaluar("Cliente frecuente compra 1 película", frecuente,
                 [{**matrix, "quantity": 1, "action": "comprar"}])
    assert f1["discount_pct"] == 10
    assert f1["total"] == round(149 * 0.9, 2)

    # 2) Pedido grande de cliente frecuente -> varios descuentos + tope
    f2 = evaluar("Cliente frecuente, pedido grande", frecuente, [
        {**padrino, "quantity": 2, "action": "comprar"},   # 398
        {**matrix, "quantity": 3, "action": "comprar"},    # 447
    ])
    assert f2["units_total"] == 5
    assert f2["discount_pct"] == 25  # 10 + 8 + 10 = 28 -> tope 25

    # 3) Película agotada -> reabastecimiento
    f3 = evaluar("Pedido con película agotada", normal, [
        {**forrest, "quantity": 2, "action": "rentar"},
    ])
    assert f3["restock"], "Debe sugerir reabastecimiento"

    # 4) Cliente no registrado
    f4 = evaluar("Cliente no registrado", None, [
        {**matrix, "quantity": 1, "action": "rentar"},
    ])
    assert f4["flags"].get("registro_sugerido") is True

    print("✅ Todos los escenarios y validaciones pasaron correctamente.")


if __name__ == "__main__":
    main()
