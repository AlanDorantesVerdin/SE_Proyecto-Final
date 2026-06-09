"""Utilidades comunes para las pruebas: base de datos temporal y LLM falso."""
from __future__ import annotations

import os
import tempfile
import unittest

from core.console import enable_utf8
from database.seed import seed

enable_utf8()  # evita errores de codificación al imprimir en Windows


class DisabledLLM:
    """LLM falso (siempre no disponible) para pruebas deterministas (solo reglas)."""
    available = False
    label = "disabled"
    provider = "disabled"
    model = ""

    def generate(self, *args, **kwargs):
        return None

    def generate_json(self, *args, **kwargs):
        return None


class DBTestCase(unittest.TestCase):
    """Caso base con una BD SQLite temporal y poblada (sin rentas de ejemplo)."""

    def setUp(self) -> None:
        fd, self.db = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        seed(self.db)  # catálogo + clientes, estado limpio

    def tearDown(self) -> None:
        try:
            os.remove(self.db)
        except OSError:
            pass
