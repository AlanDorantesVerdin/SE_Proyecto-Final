"""
Agente 1 — Atención al Cliente.

Responsabilidades (según los requisitos del proyecto):
  • Leer el mensaje del cliente.
  • Detectar la intención.
  • Obtener información relevante (consulta el catálogo en la BD).
  • Responder automáticamente.

Estrategia HÍBRIDA (sistema experto + IA moderna):
  1) Reglas (base de conocimiento): clasificación determinista y explicable.
  2) LLM (Gemini): mejora la comprensión del lenguaje natural cuando está
     disponible. Si no lo está, el agente funciona igual solo con reglas.

El resultado es un objeto `Interpretation` que incluye una TRAZA del
razonamiento (explicabilidad) y que sirve de "handoff" para el Agente 2.
"""
from __future__ import annotations

import re
import unicodedata

from core.knowledge_base import (
    ACTION_INTENTS,
    INTENT_KEYWORDS,
    NUMBER_WORDS,
    STOPWORDS,
)
from core.llm_client import LLMClient
from core.schemas import Intent, Interpretation, RequestedItem
from database.repository import (
    find_movies_by_title,
    get_customer_by_phone,
    list_movies,
)


def _normalize(text: str) -> str:
    """Pasa a minúsculas y elimina acentos para comparar de forma robusta."""
    text = (text or "").lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


class CustomerServiceAgent:
    """Agente conversacional de primera línea."""

    name = "Agente 1 — Atención al Cliente"

    def __init__(self, llm: LLMClient | None = None, db_path: str | None = None):
        self.llm = llm if llm is not None else LLMClient()
        self.db_path = db_path

    # ------------------------------------------------------------------ API
    def handle(self, text: str, customer_phone: str | None = None) -> Interpretation:
        """Procesa un mensaje del cliente y devuelve la interpretación completa."""
        interp = Interpretation(raw_text=text)
        normalized = _normalize(text)
        interp.add_trace("normalizacion", f"Texto analizado: '{normalized}'")

        # (1) Intención por REGLAS — base determinista y explicable.
        intent, confidence = self._detect_intent_rules(normalized, interp)
        interp.intent = intent
        interp.confidence = confidence
        interp.source = "rules"

        # (2) Entidades por REGLAS — coincidencias contra el catálogo.
        rule_items = self._extract_items_rules(normalized, intent, interp)

        # (3) Mejora opcional con LLM (Gemini).
        llm_data = self._llm_interpret(text, interp)
        if llm_data:
            interp.source = "hybrid"
            self._merge_llm(interp, llm_data, rule_items)
        else:
            interp.items = rule_items

        # (4) Validar cada película contra la base de datos (fuente de verdad).
        self._validate_items(interp)

        # (5) Identificar al cliente (por teléfono de WhatsApp).
        customer = get_customer_by_phone(customer_phone, self.db_path)
        if customer:
            interp.add_trace(
                "cliente",
                f"Cliente identificado: {customer['name']} "
                f"(frecuente={bool(customer['is_frequent'])}, "
                f"rentas={customer['rentals_count']})",
            )

        # (6) Construir la respuesta automática.
        interp.reply = self._compose_reply(interp, customer)
        return interp

    # -------------------------------------------------------- detección reglas
    def _detect_intent_rules(self, normalized: str,
                             interp: Interpretation) -> tuple[Intent, float]:
        """Cuenta coincidencias de palabras clave por intención."""
        scores: dict[Intent, int] = {}
        matched: dict[Intent, list[str]] = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            for kw in keywords:
                if _normalize(kw) in normalized:
                    scores[intent] = scores.get(intent, 0) + 1
                    matched.setdefault(intent, []).append(kw)

        if not scores:
            interp.add_trace("intencion", "Ninguna regla coincidió -> 'desconocido'")
            return Intent.UNKNOWN, 0.0

        # Las intenciones accionables tienen prioridad sobre saludo/despedida.
        action_scores = {i: s for i, s in scores.items() if i in ACTION_INTENTS}
        pool = action_scores or scores
        best = max(pool, key=pool.get)
        confidence = min(1.0, 0.5 + 0.2 * pool[best])
        interp.add_trace(
            "intencion",
            f"Regla: palabras {matched[best]} -> intención '{best.value}' "
            f"(confianza {confidence:.0%})",
        )
        return best, confidence

    # -------------------------------------------------------- extracción reglas
    def _extract_items_rules(self, normalized: str, intent: Intent,
                             interp: Interpretation) -> list[RequestedItem]:
        """Detecta títulos del catálogo presentes en el mensaje."""
        numbers = self._extract_numbers(normalized)
        default_action = (
            "rentar" if intent == Intent.RENT
            else "comprar" if intent == Intent.BUY
            else None
        )

        found: list[RequestedItem] = []
        for movie in list_movies(self.db_path):
            title_n = _normalize(movie["title"])
            hit = title_n in normalized
            if not hit:
                # coincidencia por palabra significativa del título
                tokens = [t for t in title_n.split()
                          if len(t) >= 4 and t not in STOPWORDS]
                hit = any(t in normalized for t in tokens)
            if hit:
                found.append(RequestedItem(
                    title_query=movie["title"],
                    quantity=1,
                    action=default_action,
                    matched=dict(movie),
                ))

        # Si hay exactamente una película y un número, asignamos la cantidad.
        if len(found) == 1 and numbers:
            found[0].quantity = numbers[0]

        if found:
            interp.add_trace(
                "entidades",
                "Reglas detectaron: "
                + ", ".join(f"{it.title_query} x{it.quantity}" for it in found),
            )
        return found

    @staticmethod
    def _extract_numbers(normalized: str) -> list[int]:
        """Extrae cantidades escritas con dígitos o con letra."""
        digits = [int(n) for n in re.findall(r"\b(\d+)\b", normalized)]
        words = [NUMBER_WORDS[w] for w in normalized.split() if w in NUMBER_WORDS]
        return digits + words

    # -------------------------------------------------------------- capa LLM
    def _llm_interpret(self, text: str, interp: Interpretation) -> dict | None:
        """
        Pide a Gemini una interpretación estructurada (JSON) en UNA sola llamada.

        Cuando la intención es 'explorar_catalogo' o 'desconocido' (preguntas
        libres), Gemini también genera la respuesta directamente en ese mismo
        JSON (campo 'reply'), evitando una segunda llamada y reduciendo el uso
        de la cuota de la API.
        """
        if not self.llm.available:
            interp.add_trace("llm", "LLM no disponible: se usan solo reglas.")
            return None

        movies = list_movies(self.db_path)
        catalog_ids = ", ".join(m["title"] for m in movies)
        catalog_detail = "\n".join(
            f"- {m['title']} ({m['genre']}, {m['year']}) "
            f"renta ${m['price_rent']:.0f} compra ${m['price_buy']:.0f} stock {m['stock']}"
            for m in movies
        )
        system = (
            "Eres el Agente de Atención al Cliente de 'CineFísico', una tienda "
            "moderna de películas físicas (DVD, Blu-ray, 4K). Eres amable, conciso "
            "y experto en cine. Respondes ÚNICAMENTE con JSON válido, sin texto extra."
        )
        prompt = (
            f"Catálogo (para identificar títulos): {catalog_ids}\n\n"
            f'Mensaje del cliente: "{text}"\n\n'
            "Devuelve un JSON con esta forma:\n"
            "{\n"
            '  "intent": "saludo|explorar_catalogo|rentar|comprar|'
            'consultar_disponibilidad|devolver|soporte|despedida|desconocido",\n'
            '  "items": [{"title": "titulo exacto del catalogo", '
            '"quantity": 1, "action": "rentar|comprar|null"}],\n'
            '  "reply": null\n'
            "}\n\n"
            "Reglas importantes:\n"
            "- 'soporte' SOLO para quejas o problemas con un pedido existente.\n"
            "- 'explorar_catalogo' para recomendaciones, preguntas de precios, "
            "formatos, géneros o cualquier pregunta general sobre la tienda.\n"
            "- 'desconocido' para temas ajenos a películas o la tienda.\n"
            "- Si intent es 'explorar_catalogo' o 'desconocido', escribe en 'reply' "
            "una respuesta útil en español (máx. 3 oraciones) usando este catálogo:\n"
            f"{catalog_detail}\n"
            "- Si intent NO es explorar_catalogo ni desconocido, deja 'reply': null.\n"
            "- Si el cliente no menciona películas del catálogo, 'items' debe ser []."
        )
        data = self.llm.generate_json(prompt, system=system)
        if not data:
            interp.add_trace("llm", "El LLM no devolvió JSON válido; se usan reglas.")
            return None
        interp.add_trace(
            "llm",
            f"Gemini interpretó intención='{data.get('intent')}', "
            f"items={len(data.get('items', []))}.",
        )
        return data

    @staticmethod
    def _parse_intent(value) -> Intent:
        try:
            return Intent(str(value).strip().lower())
        except (ValueError, AttributeError):
            return Intent.UNKNOWN

    @staticmethod
    def _clean_action(value) -> str | None:
        value = (str(value or "").strip().lower())
        return value if value in {"rentar", "comprar"} else None

    def _merge_llm(self, interp: Interpretation, data: dict,
                   rule_items: list[RequestedItem]) -> None:
        """Combina la interpretación del LLM con la de las reglas."""
        llm_intent = self._parse_intent(data.get("intent"))
        if llm_intent != Intent.UNKNOWN:
            interp.intent = llm_intent
            interp.confidence = max(interp.confidence, 0.85)

        llm_items = [
            RequestedItem(
                title_query=str(it.get("title", "")).strip(),
                quantity=max(1, int(it.get("quantity") or 1)),
                action=self._clean_action(it.get("action")),
            )
            for it in data.get("items", []) if it.get("title")
        ]
        # Preferimos los items del LLM; si no detectó ninguno, usamos las reglas.
        interp.items = llm_items or rule_items

        # Si Gemini ya generó la respuesta (para explorar_catalogo/desconocido),
        # la guardamos para usarla directamente sin segunda llamada a la API.
        llm_reply = (data.get("reply") or "").strip()
        if llm_reply:
            interp._llm_prebuilt_reply = llm_reply

    # ------------------------------------------------------------ validación
    def _validate_items(self, interp: Interpretation) -> None:
        """Confirma cada película contra el catálogo y anexa stock/precio."""
        for item in interp.items:
            if item.matched is None:
                rows = find_movies_by_title(item.title_query, self.db_path)
                if rows:
                    item.matched = dict(rows[0])
            if item.found:
                interp.add_trace(
                    "catalogo",
                    f"'{item.title_query}' -> '{item.matched['title']}' "
                    f"(stock {item.matched['stock']}, "
                    f"{'disponible' if item.available else 'insuficiente'})",
                )
            else:
                interp.add_trace(
                    "catalogo",
                    f"'{item.title_query}' no se encontró en el catálogo.",
                )

    # -------------------------------------------------------------- respuesta
    def _compose_reply(self, interp: Interpretation, customer) -> str:
        """Construye la respuesta automática usando datos reales de la BD."""
        name = ""
        if customer and customer["name"]:
            name = " " + customer["name"].split()[0]

        intent, items = interp.intent, interp.items

        if intent == Intent.GREETING and not items:
            return (f"¡Hola{name}! 👋 Soy el asistente de *CineFísico*, tu tienda "
                    "de películas. ¿Te gustaría rentar o comprar una película hoy?")

        if intent == Intent.GOODBYE and not items:
            return (f"¡Gracias por tu visita{name}! 🎬 Que disfrutes la función. "
                    "Vuelve pronto.")

        if intent == Intent.SUPPORT:
            prebuilt = getattr(interp, "_llm_prebuilt_reply", "")
            if prebuilt:
                return prebuilt
            return ("Lamento el inconveniente. Cuéntame con detalle qué ocurrió "
                    "(número de pedido o título) y con gusto lo reviso. 🛠️")

        if intent == Intent.BROWSE and not items:
            # Si Gemini ya generó la respuesta (en la misma llamada de clasificación),
            # la usamos directamente sin una segunda llamada a la API.
            prebuilt = getattr(interp, "_llm_prebuilt_reply", "")
            if prebuilt:
                return prebuilt
            destacados = [m for m in list_movies(self.db_path) if m["stock"] > 0][:5]
            listado = "\n".join(
                f"• *{m['title']}* ({m['year']}, {m['genre']}) — "
                f"renta ${m['price_rent']:.0f} / compra ${m['price_buy']:.0f}"
                for m in destacados
            )
            return (f"Estos son algunos títulos disponibles{name}:\n{listado}\n\n"
                    "¿Cuál te interesa?")

        if items:
            return self._reply_for_items(intent, items)

        if intent in (Intent.RENT, Intent.BUY):
            verbo = "rentar" if intent == Intent.RENT else "comprar"
            return f"¡Con gusto{name}! ¿Qué película te gustaría {verbo}?"

        # Fallback con IA: respuesta libre del asistente para cualquier consulta.
        # Si el LLM ya generó la respuesta en la clasificación, se reutiliza.
        prebuilt = getattr(interp, "_llm_prebuilt_reply", "")
        if prebuilt:
            return prebuilt
        return self._llm_free_reply(interp.raw_text, customer)

    def _llm_free_reply(self, text: str, customer) -> str:
        """
        Responde con Gemini cualquier mensaje que no encaja en las reglas:
        recomendaciones por género, preguntas sobre actores, dudas generales, etc.
        Si el LLM no está disponible, da la respuesta genérica de plantilla.
        """
        if not self.llm.available:
            return ("Disculpa, no estoy seguro de haberte entendido. ¿Quieres "
                    "ver el *catálogo*, *rentar* o *comprar* una película? 🎬")

        catalogo = "\n".join(
            f"- {m['title']} ({m['genre']}, {m['year']}) "
            f"renta ${m['price_rent']:.0f} compra ${m['price_buy']:.0f} "
            f"stock {m['stock']}"
            for m in list_movies(self.db_path)
        )
        cliente_info = ""
        if customer:
            cliente_info = (f"\nCliente: {customer['name']}, "
                            f"{'frecuente' if customer['is_frequent'] else 'regular'}, "
                            f"{customer['rentals_count']} rentas previas.")

        system = (
            "Eres el asistente virtual de *CineFísico*, una tienda moderna de "
            "películas en formato físico (DVD, Blu-ray, 4K). Eres amable, conciso "
            "y experto en cine. Respondes SOLO en español. Si el cliente pregunta "
            "algo fuera del tema de películas o la tienda, lo rediriges con amabilidad."
        )
        prompt = (
            f"Catálogo actual:\n{catalogo}"
            f"{cliente_info}\n\n"
            f"Mensaje del cliente: \"{text}\"\n\n"
            "Responde de forma natural y útil en máximo 3 oraciones. "
            "Puedes recomendar películas del catálogo si es relevante."
        )
        respuesta = self.llm.generate(prompt, system=system)
        return respuesta or ("Disculpa, no estoy seguro de haberte entendido. "
                             "¿Quieres ver el *catálogo*, *rentar* o *comprar*? 🎬")

    @staticmethod
    def _reply_for_items(intent: Intent, items: list[RequestedItem]) -> str:
        lines: list[str] = []
        for it in items:
            action = it.action or (
                "rentar" if intent == Intent.RENT
                else "comprar" if intent == Intent.BUY else None
            )
            if not it.found:
                lines.append(f"❓ No encontré *{it.title_query}* en el catálogo. "
                             "¿Podrías confirmar el título?")
                continue

            m = it.matched
            if it.available:
                precio = m["price_rent"] if action == "rentar" else m["price_buy"]
                verbo = ("renta" if action == "rentar"
                         else "compra" if action == "comprar" else "disponible por")
                extra = f" (pediste {it.quantity})" if it.quantity > 1 else ""
                lines.append(
                    f"✅ *{m['title']}* ({m['format']}, {m['year']}) — "
                    f"{verbo} ${precio:.0f}. Hay {m['stock']} en existencia{extra}."
                )
            elif m["stock"] == 0:
                lines.append(f"⚠️ *{m['title']}* está agotado por ahora. "
                             "¿Quieres que te avise cuando vuelva a entrar?")
            else:
                lines.append(
                    f"⚠️ De *{m['title']}* solo quedan {m['stock']} y pediste "
                    f"{it.quantity}. ¿Te sirve esa cantidad?"
                )

        if any(it.available for it in items):
            lines.append("\n¿Confirmo tu pedido? ✅")
        return "\n".join(lines)
