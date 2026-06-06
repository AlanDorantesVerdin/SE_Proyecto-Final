"""
Demostración del orquestador: conversación completa por los 3 agentes (Día 6).

Ejecuta:
    python run_orchestrator.py

Simula una conversación de WhatsApp: el cliente pide, el sistema explica y pide
confirmación; según la respuesta (SÍ/NO) el pedido se guarda o se cancela.
"""
from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from core.console import enable_utf8
from database.repository import count_orders
from database.seed import seed
from orchestrator import Orchestrator

enable_utf8()

FRECUENTE = "+5216561234567"   # Alan (cliente frecuente, en el seed)


def conversar(orch: Orchestrator, phone: str, mensajes: list[str]) -> None:
    for msg in mensajes:
        print(f"🧑 Cliente: {msg}")
        print(f"🤖 Sistema:\n{orch.handle_message(msg, phone=phone)}\n")


def main() -> None:
    seed()  # estado limpio (también reinicia pedidos)
    orch = Orchestrator()

    print("=" * 64)
    print("CONVERSACIÓN 1 — el cliente confirma el pedido")
    print("=" * 64)
    conversar(orch, FRECUENTE, [
        "Hola, buenas tardes",
        "quiero comprar 2 El Padrino y 3 The Matrix",
        "sí",
    ])
    assert count_orders() == 1, "Tras confirmar debe existir 1 pedido guardado"

    print("=" * 64)
    print("CONVERSACIÓN 2 — el cliente cancela el pedido")
    print("=" * 64)
    conversar(orch, FRECUENTE, [
        "ahora quiero rentar Shrek",
        "no",
    ])
    assert count_orders() == 1, "Tras cancelar NO debe crearse un pedido nuevo"

    print("✅ Orquestador verificado: flujo 1 -> 2 -> 3 con confirmación y cancelación.")


if __name__ == "__main__":
    main()
