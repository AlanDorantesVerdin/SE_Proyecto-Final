"""
Prueba local del Agente 1 (Atención al Cliente) por terminal.

Uso:
    python run_cli.py            # modo interactivo (chateas con el agente)
    python run_cli.py --demo     # ejecuta una conversación de ejemplo

Antes de la primera ejecución se puebla la base de datos automáticamente.
"""
from __future__ import annotations

import sys

from dotenv import load_dotenv

load_dotenv()  # carga GEMINI_API_KEY y demás variables desde .env

from agents.agent_customer import CustomerServiceAgent  # noqa: E402
from core.console import enable_utf8                     # noqa: E402
from core.llm_client import LLMClient                   # noqa: E402
from database.repository import count_movies            # noqa: E402
from database.seed import seed                          # noqa: E402

enable_utf8()

# Teléfono simulado: corresponde a un cliente frecuente del seed.
DEMO_PHONE = "+5216561234567"

DEMO_MESSAGES = [
    "Hola, buenas tardes",
    "¿Tienen Matrix? quiero rentar 2",
    "Quiero comprar El Padrino y también rentar Forrest Gump",
    "Me interesa una de superhéroes de Marvel",
    "Gracias, eso es todo",
]


def _ensure_data() -> None:
    if count_movies() == 0:
        seed()


def print_interpretation(interp) -> None:
    print("─" * 64)
    print(f"🧠 Intención : {interp.intent.value}  "
          f"(confianza {interp.confidence:.0%} · fuente: {interp.source})")
    if interp.items:
        print("🎬 Películas detectadas:")
        for it in interp.items:
            if it.found:
                estado = "disponible" if it.available else "AGOTADO/insuficiente"
                print(f"   • {it.matched['title']} x{it.quantity} "
                      f"[{it.action or '—'}] → {estado}")
            else:
                print(f"   • '{it.title_query}' x{it.quantity} → no encontrado")
    print("🔎 Traza de razonamiento (explicabilidad):")
    for step in interp.trace:
        print(f"   - [{step.rule}] {step.detail}")
    print(f"\n💬 Agente:\n{interp.reply}")
    print("─" * 64 + "\n")


def run_demo(agent: CustomerServiceAgent) -> None:
    for msg in DEMO_MESSAGES:
        print(f"\n🧑 Cliente: {msg}")
        print_interpretation(agent.handle(msg, customer_phone=DEMO_PHONE))


def run_interactive(agent: CustomerServiceAgent) -> None:
    print("Escribe un mensaje como cliente. Comandos: 'salir' para terminar.\n")
    while True:
        try:
            text = input("🧑 Cliente> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n¡Hasta luego!")
            break
        if not text:
            continue
        if text.lower() in {"salir", "exit", "quit"}:
            print("¡Hasta luego!")
            break
        print_interpretation(agent.handle(text, customer_phone=DEMO_PHONE))


def main() -> None:
    _ensure_data()
    llm = LLMClient()
    agent = CustomerServiceAgent(llm=llm)

    print("=" * 64)
    print("  CineFísico — Agente 1: Atención al Cliente")
    print(f"  LLM (Gemini): {'ACTIVO ✅' if llm.available else 'INACTIVO (solo reglas) ⚙️'}")
    print("=" * 64)

    if "--demo" in sys.argv:
        run_demo(agent)
    else:
        run_interactive(agent)


if __name__ == "__main__":
    main()
