"""Pruebas del motor de inferencia y las reglas de negocio."""
import unittest

from core.business_rules import build_order_rules, make_order_facts
from core.inference_engine import InferenceEngine

FRECUENTE = {"name": "Alan", "is_frequent": True, "rentals_count": 7}
NORMAL = {"name": "Ana", "is_frequent": False, "rentals_count": 0}
MATRIX = {"title": "The Matrix", "stock": 8, "price_rent": 39, "price_buy": 149}
PADRINO = {"title": "El Padrino", "stock": 3, "price_rent": 49, "price_buy": 199}
AGOTADA = {"title": "Forrest Gump", "stock": 0, "price_rent": 35, "price_buy": 129}


def _run(customer, items, overdue=0):
    facts = make_order_facts(customer, items)
    facts["overdue_count"] = overdue
    return InferenceEngine(build_order_rules()).run(facts)


class TestInference(unittest.TestCase):
    def test_descuento_cliente_frecuente(self):
        r = _run(FRECUENTE, [{**MATRIX, "quantity": 1, "action": "comprar"}])
        self.assertEqual(r.facts["discount_pct"], 10)
        self.assertEqual(r.facts["total"], round(149 * 0.9, 2))

    def test_sin_descuento_cliente_normal(self):
        r = _run(NORMAL, [{**MATRIX, "quantity": 1, "action": "comprar"}])
        self.assertEqual(r.facts["discount_pct"], 0)

    def test_descuentos_apilados_con_tope(self):
        r = _run(FRECUENTE, [
            {**PADRINO, "quantity": 2, "action": "comprar"},   # 398
            {**MATRIX, "quantity": 3, "action": "comprar"},    # 447
        ])
        self.assertEqual(r.facts["units_total"], 5)
        self.assertEqual(r.facts["discount_pct"], 25)   # 10+8+10=28 -> tope 25

    def test_reabastecimiento(self):
        r = _run(NORMAL, [{**AGOTADA, "quantity": 2, "action": "rentar"}])
        self.assertTrue(r.facts["restock"])
        self.assertEqual(r.facts["restock"][0]["title"], "Forrest Gump")

    def test_rentas_vencidas_dispara_regla(self):
        r = _run(FRECUENTE, [{**MATRIX, "quantity": 1, "action": "rentar"}], overdue=2)
        self.assertIn("rentas_vencidas", [fr.name for fr in r.fired])

    def test_total_renta_sin_descuento(self):
        r = _run(NORMAL, [{**MATRIX, "quantity": 1, "action": "rentar"}])
        self.assertEqual(r.facts["total"], 39)


if __name__ == "__main__":
    unittest.main()
