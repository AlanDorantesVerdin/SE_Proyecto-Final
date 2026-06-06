"""
Servidor FastAPI que expone el Agente 1 por WhatsApp (Twilio).

Cómo ejecutar en local:
    uvicorn api.main:app --reload --port 8000

Luego expón el puerto a Internet con un túnel y configura esa URL pública
en el sandbox de Twilio (campo "When a message comes in"):
    ngrok http 8000
    -> https://XXXX.ngrok-free.app/webhook/whatsapp

Endpoints:
    GET  /                   -> estado del servicio (health check)
    POST /webhook/whatsapp   -> recibe mensajes de WhatsApp y responde
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from core.console import enable_utf8  # noqa: E402

enable_utf8()

from fastapi import FastAPI, Request, Response  # noqa: E402

from channels.whatsapp_twilio import (  # noqa: E402
    build_reply,
    is_valid_signature,
    parse_incoming,
)
from core.llm_client import LLMClient  # noqa: E402
from database.repository import count_movies  # noqa: E402
from database.seed import seed  # noqa: E402
from orchestrator import Orchestrator  # noqa: E402

# Inicialización única al arrancar el servidor.
if count_movies() == 0:
    seed()
llm = LLMClient()
orchestrator = Orchestrator(llm=llm)

app = FastAPI(title="CineFísico — WhatsApp (3 agentes)")


@app.get("/")
def health() -> dict:
    """Health check: confirma que el servicio está vivo."""
    return {
        "status": "ok",
        "service": "CineFísico",
        "agents": "1 (atención) + 2 (pedido) + 3 (explicador)",
        "llm": "activo" if llm.available else "solo reglas",
    }


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request) -> Response:
    """Recibe un mensaje de WhatsApp (vía Twilio) y responde con el flujo de 3 agentes."""
    form = dict(await request.form())

    # Seguridad opcional: validar que la petición proviene de Twilio.
    if os.getenv("TWILIO_VALIDATE", "false").lower() == "true":
        base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
        url = (base + request.url.path) if base else str(request.url)
        signature = request.headers.get("X-Twilio-Signature", "")
        if not is_valid_signature(url, form, signature):
            return Response(status_code=403, content="Firma de Twilio inválida")

    text, phone = parse_incoming(form)
    if not text:
        reply = "Envíame un mensaje de texto y con gusto te ayudo. 🎬"
    else:
        reply = orchestrator.handle_message(text, phone=phone)
        # Traza en consola, útil durante la demostración.
        print(f"[WhatsApp] {phone}: {text!r}")

    return Response(content=build_reply(reply), media_type="application/xml")
