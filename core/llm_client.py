"""
Cliente de LLM (Gemini) con DEGRADACIÓN ELEGANTE.

Filosofía de diseño: el sistema experto debe funcionar SIEMPRE, incluso sin
conexión o sin API key válida. Por eso el LLM es un "asistente opcional":
- Si hay API key válida -> mejora la comprensión del lenguaje natural.
- Si no la hay -> el agente sigue operando solo con sus reglas.

Esto evita que la demostración se caiga por un problema de red o credenciales.
"""
from __future__ import annotations

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

# La importación se protege para que el proyecto no truene si el paquete
# aún no está instalado (modo solo-reglas).
try:
    from google import genai
    from google.genai import types
    _GENAI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _GENAI_AVAILABLE = False


_PLACEHOLDERS = {"", "pega_aqui_tu_api_key", "tu_api_key_aqui"}


class LLMClient:
    """Envoltorio mínimo sobre el SDK de Gemini."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model = model or os.getenv("LLM_MODEL", "gemini-2.5-flash")
        self._client = None

        if not _GENAI_AVAILABLE:
            logger.info("SDK google-genai no disponible: se usará solo reglas.")
            return
        if self.api_key in _PLACEHOLDERS:
            logger.info("Sin GEMINI_API_KEY válida: se usará solo reglas.")
            return
        try:
            self._client = genai.Client(api_key=self.api_key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo inicializar Gemini (%s). Solo reglas.", exc)
            self._client = None

    @property
    def available(self) -> bool:
        """True si el LLM está listo para usarse."""
        return self._client is not None

    def generate(self, prompt: str, system: str | None = None,
                 json_mode: bool = False) -> str | None:
        """Genera texto. Devuelve None si el LLM no está disponible o falla."""
        if not self.available:
            return None
        try:
            config = types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.2,
                response_mime_type="application/json" if json_mode else None,
            )
            resp = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            return (resp.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error llamando a Gemini: %s", exc)
            return None

    def generate_json(self, prompt: str, system: str | None = None) -> dict | None:
        """Pide una respuesta JSON al modelo y la parsea de forma robusta."""
        raw = self.generate(prompt, system=system, json_mode=True)
        if not raw:
            return None
        return _extract_json(raw)


def _extract_json(text: str) -> dict | None:
    """Extrae el primer objeto JSON de un texto (tolera ```json ... ```)."""
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None
