"""Pruebas de persistencia del pedido (guardado, stock, rentas, reabastecimiento)."""
from agents.agent_orders import OrderGeneratorAgent
from core.schemas import Intent, Interpretation, RequestedItem
from database.repository import (
    count_orders,
    get_movie_by_title,
    list_rentals,
    list_restock,
)
from tests.base import DBTestCase

FRECUENTE = "+5216561234567"


class TestPersistence(DBTestCase):
    def setUp(self):
        super().setUp()
        self.agent2 = OrderGeneratorAgent(db_path=self.db)

    def _build_order(self):
        interp = Interpretation(raw_text="test", intent=Intent.RENT)
        interp.items = [
            RequestedItem(title_query="The Matrix", quantity=2, action="rentar",
                          matched=dict(get_movie_by_title("The Matrix", self.db))),
            RequestedItem(title_query="Forrest Gump", quantity=1, action="rentar",
                          matched=dict(get_movie_by_title("Forrest Gump", self.db))),
        ]
        return self.agent2.process(interp, customer_phone=FRECUENTE)

    def test_confirmar_guarda_y_descuenta_stock(self):
        stock_antes = get_movie_by_title("The Matrix", self.db)["stock"]
        order = self.agent2.confirm(self._build_order(), customer_phone=FRECUENTE)
        self.assertIsNotNone(order.order_id)
        self.assertEqual(count_orders(self.db), 1)
        stock_despues = get_movie_by_title("The Matrix", self.db)["stock"]
        self.assertEqual(stock_despues, stock_antes - 2)

    def test_confirmar_crea_renta_y_reabastecimiento(self):
        self.agent2.confirm(self._build_order(), customer_phone=FRECUENTE)
        rentas = list_rentals(self.db)
        restock = list_restock(self.db)
        self.assertTrue(any(r["title"] == "The Matrix" for r in rentas))
        self.assertTrue(any(r["title"] == "Forrest Gump" for r in restock))
