"""
Interfaz web (Streamlit) de CineFísico.

Chat con el sistema de 3 agentes + panel lateral con las inferencias en vivo,
el catálogo y el cliente simulado. Reutiliza el mismo orquestador que WhatsApp.

Ejecuta DESDE LA RAÍZ del proyecto:
    streamlit run ui/app.py
"""
from __future__ import annotations

import os
import sys

# Permite importar los paquetes del proyecto al ejecutar con `streamlit run`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from core.llm_client import LLMClient
from database.repository import count_movies, list_movies
from database.seed import seed
from orchestrator import Orchestrator

# ---- Inicialización ----
if count_movies() == 0:
    seed()

st.set_page_config(page_title="CineFísico", page_icon="🎬", layout="wide")

# Clientes simulados (el teléfono determina descuentos por cliente frecuente).
CUSTOMERS = {
    "Alan (cliente frecuente)": "+5216561234567",
    "María (cliente normal)": "+5216567654321",
    "Invitado (no registrado)": "+5210000000000",
}

if "orch" not in st.session_state:
    st.session_state.orch = Orchestrator()
    st.session_state.messages = []

orch: Orchestrator = st.session_state.orch

# ---- Barra lateral ----
with st.sidebar:
    st.title("🎬 CineFísico")
    st.caption("Sistema experto · 3 agentes inteligentes")

    llm_on = LLMClient().available
    st.markdown(f"**IA (Gemini):** {'🟢 activa' if llm_on else '🟠 solo reglas'}")

    cliente = st.selectbox("Cliente (simulado):", list(CUSTOMERS))
    st.session_state.phone = CUSTOMERS[cliente]

    st.divider()
    st.subheader("🧠 Inferencias del último pedido")
    last = getattr(orch, "last_order", None)
    if last and last.reasoning:
        for paso in last.reasoning:
            st.markdown(f"- {paso}")
        if last.restock:
            faltantes = ", ".join(x["title"] for x in last.restock)
            st.warning(f"Reabastecer: {faltantes}")
    else:
        st.caption("Aún no hay inferencias. Pide una película para verlas.")

    st.divider()
    with st.expander("🎞️ Ver catálogo"):
        for m in list_movies():
            estado = f"{m['stock']} en stock" if m["stock"] > 0 else "agotado"
            st.markdown(
                f"**{m['title']}** ({m['year']}) — renta ${m['price_rent']:.0f} / "
                f"compra ${m['price_buy']:.0f} · _{estado}_"
            )

    if st.button("🔄 Reiniciar conversación"):
        st.session_state.orch = Orchestrator()
        st.session_state.messages = []
        st.rerun()

# ---- Chat principal ----
st.title("Asistente de CineFísico 🎬")
st.caption("Escribe como cliente: «Hola» · «quiero rentar 2 Matrix» · «sí» para confirmar")

for role, text in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(text)

prompt = st.chat_input("Escribe tu mensaje…")
if prompt:
    st.session_state.messages.append(("user", prompt))
    reply = orch.handle_message(prompt, phone=st.session_state.phone)
    st.session_state.messages.append(("assistant", reply))
    st.rerun()
