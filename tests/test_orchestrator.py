"""Pruebas del flujo conversacional completo (orquestador de los 3 agentes)."""
from database.repository import count_orders
from orchestrator import Orchestrator
from tests.base import DBTestCase, DisabledLLM

FRECUENTE = "+5216561234567"


class TestOrchestrator(DBTestCase):
    def setUp(self):
        super().setUp()
        self.orch = Orchestrator(db_path=self.db, llm=DisabledLLM())

    def test_flujo_confirmar_guarda_pedido(self):
        r1 = self.orch.handle_message("quiero rentar 2 The Matrix", phone=FRECUENTE)
        self.assertIn("Confirmas", r1)
        r2 = self.orch.handle_message("sí", phone=FRECUENTE)
        self.assertIn("confirmado", r2.lower())
        self.assertEqual(count_orders(self.db), 1)

    def test_flujo_cancelar_no_guarda(self):
        self.orch.handle_message("quiero comprar El Padrino", phone=FRECUENTE)
        r = self.orch.handle_message("no", phone=FRECUENTE)
        self.assertIn("cancel", r.lower())
        self.assertEqual(count_orders(self.db), 0)

    def test_saludo_no_genera_pedido(self):
        r = self.orch.handle_message("Hola", phone=FRECUENTE)
        self.assertEqual(count_orders(self.db), 0)
        self.assertNotIn("Confirmas", r)
