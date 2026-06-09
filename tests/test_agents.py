"""Pruebas de los agentes 1 y 2 (modo solo-reglas, deterministas)."""
from agents.agent_customer import CustomerServiceAgent
from agents.agent_orders import OrderGeneratorAgent
from core.schemas import Intent, Interpretation, RequestedItem
from tests.base import DBTestCase, DisabledLLM

FRECUENTE = "+5216561234567"


class TestAgentCustomer(DBTestCase):
    def setUp(self):
        super().setUp()
        self.agent = CustomerServiceAgent(llm=DisabledLLM(), db_path=self.db)

    def test_saludo(self):
        interp = self.agent.handle("Hola, buenas tardes", customer_phone=FRECUENTE)
        self.assertEqual(interp.intent, Intent.GREETING)

    def test_rentar_detecta_pelicula_y_cantidad(self):
        interp = self.agent.handle("quiero rentar 2 The Matrix", customer_phone=FRECUENTE)
        self.assertEqual(interp.intent, Intent.RENT)
        self.assertEqual(len(interp.items), 1)
        self.assertEqual(interp.items[0].matched["title"], "The Matrix")
        self.assertEqual(interp.items[0].quantity, 2)

    def test_comprar_detecta_pelicula(self):
        interp = self.agent.handle("comprar El Padrino", customer_phone=FRECUENTE)
        self.assertEqual(interp.intent, Intent.BUY)
        self.assertTrue(any(it.matched and it.matched["title"] == "El Padrino"
                            for it in interp.items))


class TestAgentOrders(DBTestCase):
    def setUp(self):
        super().setUp()
        self.agent2 = OrderGeneratorAgent(db_path=self.db)

    def _interp(self, items, intent=Intent.BUY):
        interp = Interpretation(raw_text="test", intent=intent)
        interp.items = items
        return interp

    def test_pedido_cliente_frecuente_aplica_descuento(self):
        item = RequestedItem(
            title_query="The Matrix", quantity=1, action="comprar",
            matched={"title": "The Matrix", "stock": 8, "price_rent": 39, "price_buy": 149},
        )
        order = self.agent2.process(self._interp([item]), customer_phone=FRECUENTE)
        self.assertEqual(order.discount_pct, 10)
        self.assertEqual(order.total, round(149 * 0.9, 2))

    def test_pedido_agotado_sugiere_reabastecimiento(self):
        item = RequestedItem(
            title_query="Forrest Gump", quantity=2, action="rentar",
            matched={"title": "Forrest Gump", "stock": 0, "price_rent": 35, "price_buy": 129},
        )
        order = self.agent2.process(self._interp([item], Intent.RENT),
                                    customer_phone=FRECUENTE)
        self.assertTrue(order.restock)
