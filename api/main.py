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

import json  # noqa: E402
from pathlib import Path  # noqa: E402

from fastapi import FastAPI, Request, Response  # noqa: E402
from fastapi.responses import (  # noqa: E402
    FileResponse,
    HTMLResponse,
    PlainTextResponse,
)

from channels.whatsapp_twilio import (  # noqa: E402
    build_reply,
    is_valid_signature,
    parse_incoming,
)
from core.llm_client import LLMClient  # noqa: E402
from database.repository import (  # noqa: E402
    count_movies,
    reject_order,
    validate_order,
)
from database.seed import seed  # noqa: E402
from orchestrator import Orchestrator  # noqa: E402
from webpanel.data import build_store_data  # noqa: E402

# Inicialización al arrancar (siembra datos de demostración si la BD está vacía).
if count_movies() == 0:
    seed(with_samples=True)
llm = LLMClient()
orchestrator = Orchestrator(llm=llm)

STATIC_DIR = Path(__file__).resolve().parent.parent / "webpanel" / "static"
_MEDIA = {".css": "text/css", ".js": "application/javascript",
          ".jsx": "application/javascript", ".html": "text/html"}

app = FastAPI(title="REBOBINA — CineFísico (WhatsApp + Panel)")


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    """Página de inicio: enlaza al panel de administración."""
    return HTMLResponse(
        "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>REBOBINA</title><style>"
        "body{font-family:'Segoe UI',Arial,sans-serif;background:#1b1814;color:#f4ece0;"
        "display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0}"
        ".c{text-align:center}h1{font-size:44px;color:#b9802b;margin:0 0 6px;letter-spacing:1px}"
        "p{color:#bcae98}a{display:inline-block;margin-top:24px;padding:12px 28px;"
        "background:#b9802b;color:#1b1814;text-decoration:none;border-radius:8px;font-weight:700}"
        "</style></head><body><div class='c'><h1>REBOBINA</h1>"
        "<p>Renta &amp; Venta de películas — panel de administración</p>"
        "<a href='/panel/'>Abrir el panel &rarr;</a></div></body></html>"
    )


@app.get("/health")
def health() -> dict:
    """Health check (JSON): confirma que el servicio está vivo."""
    return {
        "status": "ok",
        "service": "REBOBINA / CineFísico",
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


# ============================ PANEL WEB (REBOBINA) ============================
@app.get("/panel/", response_class=FileResponse)
def panel_home():
    """Sirve el panel de administración (aplicación React)."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/panel/data.js")
def panel_data() -> PlainTextResponse:
    """Emite los datos del panel (window.STORE_DATA) desde la base de datos real."""
    data = build_store_data()
    body = "window.STORE_DATA = " + json.dumps(data, ensure_ascii=False) + ";"
    return PlainTextResponse(body, media_type="application/javascript")


@app.post("/panel/api/validate")
async def panel_validate(request: Request) -> dict:
    """Valida (confirma) o rechaza un pedido pendiente desde el panel."""
    body = await request.json()
    order_id = int(body.get("order_id"))
    action = str(body.get("action", "")).lower()
    if action in ("aprobado", "validar", "confirmar"):
        validate_order(order_id)
        return {"ok": True, "status": "confirmado"}
    if action in ("rechazado", "rechazar"):
        reject_order(order_id)
        return {"ok": True, "status": "rechazado"}
    return {"ok": False, "error": "acción desconocida"}


@app.get("/panel/{filename}")
def panel_static(filename: str):
    """Sirve los archivos estáticos del panel (CSS, JSX)."""
    target = (STATIC_DIR / filename).resolve()
    if not str(target).startswith(str(STATIC_DIR)) or not target.is_file():
        return Response(status_code=404, content="No encontrado")
    media = _MEDIA.get(target.suffix, "application/octet-stream")
    return FileResponse(target, media_type=media)
