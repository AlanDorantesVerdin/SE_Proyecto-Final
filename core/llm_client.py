"""
Cliente de LLM con soporte para DOS proveedores y DEGRADACIÓN ELEGANTE:

- **ollama**  -> modelo local (sin límites de cuota). Requiere instalar Ollama
                 y descargar un modelo (p. ej. `ollama pull llama3.2`).
- **gemini**  -> modelo en la nube. Requiere GEMINI_API_KEY (cuota gratuita
                 limitada).

El proveedor se elige con la variable de entorno LLM_PROVIDER (ollama | gemini).
Si el proveedor elegido no está disponible, el sistema sigue funcionando en
modo SOLO REGLAS, sin caerse. Así la demostración nunca depende de la red.
"""
from __future__ import annotations

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

# httpx (ya es dependencia del proyecto) se usa para hablar con Ollama por REST.
try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:  # pragma: no cover
    _HTTPX_AVAILABLE = False

# El SDK de Gemini es opcional: solo se necesita si LLM_PROVIDER=gemini.
try:
    from google import genai
    from google.genai import types
    _GENAI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _GENAI_AVAILABLE = False

_PLACEHOLDERS = {"", "pega_aqui_tu_api_key", "tu_api_key_aqui"}


class LLMClient:
    """Cliente unificado: usa Ollama o Gemini según LLM_PROVIDER."""

    def __init__(self, provider: str | None = None, model: str | None = None,
                 api_key: str | None = None):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "ollama")).lower()
        self._ready = False
        self.model = ""
        if self.provider == "ollama":
            self._init_ollama(model)
        else:
            self._init_gemini(model, api_key)

    # ------------------------------------------------------------- Ollama
    def _init_ollama(self, model: str | None) -> None:
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        if not _HTTPX_AVAILABLE:
            logger.info("httpx no disponible; no se puede usar Ollama.")
            return
        try:
            resp = httpx.get(f"{self.host}/api/tags", timeout=2.0)
            self._ready = resp.status_code == 200
        except Exception:  # noqa: BLE001
            logger.info("Servidor Ollama no responde en %s; modo solo-reglas.", self.host)

    def _ollama_generate(self, prompt: str, system: str | None,
                         json_mode: bool) -> str | None:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        if json_mode:
            payload["format"] = "json"
        try:
            resp = httpx.post(f"{self.host}/api/chat", json=payload, timeout=120.0)
            resp.raise_for_status()
            return (resp.json()["message"]["content"] or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error llamando a Ollama: %s", exc)
            return None

    # ------------------------------------------------------------- Gemini
    def _init_gemini(self, model: str | None, api_key: str | None) -> None:
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model = model or os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
        self._client = None
        if not _GENAI_AVAILABLE or self.api_key in _PLACEHOLDERS:
            logger.info("Gemini no disponible (sin SDK o sin API key); solo reglas.")
            return
        try:
            self._client = genai.Client(api_key=self.api_key)
            self._ready = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo inicializar Gemini (%s). Solo reglas.", exc)

    def _gemini_generate(self, prompt: str, system: str | None,
                         json_mode: bool) -> str | None:
        try:
            config = types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.2,
                response_mime_type="application/json" if json_mode else None,
            )
            resp = self._client.models.generate_content(
                model=self.model, contents=prompt, config=config,
            )
            return (resp.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error llamando a Gemini: %s", exc)
            return None

    # -------------------------------------------------------- API pública
    @property
    def available(self) -> bool:
        """True si el proveedor elegido está listo para usarse."""
        return self._ready

    @property
    def label(self) -> str:
        """Etiqueta legible del proveedor activo (para mostrar en la UI/CLI)."""
        return f"{self.provider} ({self.model})" if self._ready else "solo reglas"

    def generate(self, prompt: str, system: str | None = None,
                 json_mode: bool = False) -> str | None:
        """Genera texto. Devuelve None si el LLM no está disponible o falla."""
        if not self._ready:
            return None
        if self.provider == "ollama":
            return self._ollama_generate(prompt, system, json_mode)
        return self._gemini_generate(prompt, system, json_mode)

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
