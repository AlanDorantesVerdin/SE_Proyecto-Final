"""
Adaptador del canal WhatsApp mediante Twilio (sandbox o número productivo).

El agente es independiente del canal: este módulo solo traduce entre el
formato de Twilio y nuestro agente.
  • parse_incoming  -> extrae (texto, teléfono) del formulario que envía Twilio
  • build_reply     -> construye la respuesta TwiML (XML) que Twilio entrega
  • is_valid_signature -> valida la firma del webhook (seguridad)

Twilio envía el remitente como 'whatsapp:+5216561234567'; aquí quitamos el
prefijo 'whatsapp:' para que coincida con el formato de teléfono de la BD.
"""
from __future__ import annotations

import os

from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse


def parse_incoming(form: dict) -> tuple[str, str]:
    """Extrae (texto, teléfono) de los parámetros que envía Twilio."""
    body = (form.get("Body") or "").strip()
    sender = (form.get("From") or "").replace("whatsapp:", "").strip()
    return body, sender


def build_reply(text: str) -> str:
    """Construye la respuesta TwiML que Twilio entregará al cliente."""
    twiml = MessagingResponse()
    twiml.message(text)
    return str(twiml)


def is_valid_signature(url: str, params: dict, signature: str) -> bool:
    """Valida la cabecera X-Twilio-Signature para asegurar que viene de Twilio."""
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    if not token:
        return False
    return RequestValidator(token).validate(url, params, signature or "")
