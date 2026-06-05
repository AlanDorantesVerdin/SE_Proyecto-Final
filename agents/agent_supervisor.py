"""
Agente 3 — Supervisor / Explicador.

Toma el pedido generado por el Agente 2 y:
  • Genera un resumen de la venta.
  • Explica las decisiones e inferencias realizadas.
  • Solicita la validación final del cliente.

La explicación se construye a partir del razonamiento REAL (las reglas que de
verdad se dispararon en el motor de inferencia), de modo que es fiel a lo que el
sistema hizo. Esto es la EXPLICABILIDAD que pide el proyecto.
"""
from __future__ import annotations

from core.schemas import Order, SupervisorReport

_ACCION_TEXTO = {"rentar": "renta", "comprar": "compra"}


class SupervisorAgent:
    """Resume, explica y pide validación del pedido."""

    name = "Agente 3 — Supervisor / Explicador"

    def review(self, order: Order) -> SupervisorReport:
        """Produce el reporte explicativo a partir del pedido."""
        if order.status == "sin_items" or not order.lines:
            return SupervisorReport(
                summary="No hay pedido que resumir.",
                decisions=order.reasoning or ["No se identificaron productos del catálogo."],
                validation_request="",
                message=("No pude identificar películas de nuestro catálogo en tu "
                         "solicitud. ¿Me confirmas el título exacto? 🎬"),
                requires_attention=True,
            )

        summary = self._build_summary(order)

        decisions = list(order.reasoning)
        if order.restock:
            faltantes = ", ".join(r["title"] for r in order.restock)
            decisions.append(
                f"Atención: no hay stock suficiente de {faltantes}; "
                "se generó una sugerencia de reabastecimiento."
            )

        validation = ("¿Confirmas tu pedido? Responde *SÍ* para finalizar "
                      "o *NO* para ajustarlo.")
        message = self._build_message(order, summary, decisions, validation)

        return SupervisorReport(
            summary=summary,
            decisions=decisions,
            validation_request=validation,
            message=message,
            requires_attention=bool(order.restock),
        )

    @staticmethod
    def _build_summary(order: Order) -> str:
        disponibles = [ln for ln in order.lines if ln.available]
        if not disponibles:
            return "• (sin artículos disponibles en este momento)"
        return "\n".join(
            f"• {ln.quantity}x {ln.title} "
            f"({_ACCION_TEXTO.get(ln.action, ln.action)}) — "
            f"${ln.unit_price:.0f} c/u = ${ln.line_total:.0f}"
            for ln in disponibles
        )

    @staticmethod
    def _build_message(order: Order, summary: str, decisions: list[str],
                       validation: str) -> str:
        numeradas = "\n".join(f"{i}. {d}" for i, d in enumerate(decisions, 1))
        partes = [
            f"🎬 *Resumen de tu pedido* — {order.customer_name}",
            "",
            "🛒 Detalle:",
            summary,
            "",
            f"💵 Subtotal: ${order.subtotal:.0f}",
        ]
        if order.discount_amount:
            partes.append(
                f"🏷️ Descuento: {order.discount_pct:.0f}% (−${order.discount_amount:.0f})"
            )
        partes.append(f"✅ *Total: ${order.total:.0f}*")
        partes += ["", "🧠 *¿Cómo llegué a esto?* (decisiones del sistema)", numeradas]
        if order.restock:
            faltantes = ", ".join(
                f"{r['title']} (faltan {r['faltan']})" for r in order.restock
            )
            partes += ["", f"⚠️ Reabastecimiento sugerido: {faltantes}"]
        partes += ["", validation]
        return "\n".join(partes)
