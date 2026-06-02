"""
Base de reglas de negocio del Agente 2 (Generador de Pedido).

Aquí vive el CONOCIMIENTO EXPERTO sobre precios, descuentos y stock de la tienda
de películas. Las reglas son explícitas y editables: para cambiar la política
comercial se editan aquí, sin tocar el motor de inferencia ni los agentes.

Cada regla incluye una descripción IF/THEN legible y produce una explicación
concreta que alimenta la EXPLICABILIDAD del sistema (la usará el Agente 3).
"""
from __future__ import annotations

from core.inference_engine import Rule

# ----- Parámetros de la política comercial (fáciles de ajustar) -----
DESCUENTO_FRECUENTE = 10       # % para clientes frecuentes
DESCUENTO_VOLUMEN = 8         # % si se piden muchas unidades
UNIDADES_PARA_VOLUMEN = 5     # umbral de unidades para el descuento por volumen
DESCUENTO_MONTO = 10          # % si el subtotal es alto
MONTO_PARA_DESCUENTO = 300    # umbral de subtotal ($) para el descuento por monto
DESCUENTO_MAXIMO = 25         # tope del descuento acumulado (%)


def make_order_facts(customer: dict | None, items: list[dict]) -> dict:
    """
    Construye la 'memoria de trabajo' del motor a partir del cliente y los ítems.

    Cada item de entrada debe traer: title, quantity, action ('rentar'|'comprar'),
    stock, price_rent, price_buy. Se calcula precio, disponibilidad y subtotal.
    """
    enriquecidos = []
    for it in items:
        action = (it.get("action") or "comprar").lower()
        cantidad = max(1, int(it.get("quantity", 1)))
        stock = int(it.get("stock", 0))
        precio = float(it["price_rent"] if action == "rentar" else it["price_buy"])
        enriquecidos.append({
            "title": it["title"],
            "quantity": cantidad,
            "action": action,
            "stock": stock,
            "unit_price": precio,
            "line_total": precio * cantidad,
            "available": stock >= cantidad,
        })

    subtotal = sum(it["line_total"] for it in enriquecidos if it["available"])
    unidades = sum(it["quantity"] for it in enriquecidos if it["available"])

    return {
        "customer": customer,
        "items": enriquecidos,
        "subtotal": subtotal,
        "units_total": unidades,
        "discount_pct": 0,
        "restock": [],
        "flags": {},
    }


# ----------------------------- Acciones (parte THEN) -----------------------------
def _then_restock(f: dict) -> str:
    faltantes = [it for it in f["items"] if not it["available"]]
    f["restock"] = [
        {"title": it["title"], "faltan": max(0, it["quantity"] - it["stock"])}
        for it in faltantes
    ]
    detalle = ", ".join(
        f"{it['title']} (stock {it['stock']}, pidió {it['quantity']})"
        for it in faltantes
    )
    return f"Stock insuficiente: {detalle}. Se sugiere reabastecer."


def _then_frecuente(f: dict) -> str:
    f["discount_pct"] += DESCUENTO_FRECUENTE
    rentas = f["customer"].get("rentals_count", 0)
    return (f"Cliente frecuente ({rentas} rentas previas): "
            f"+{DESCUENTO_FRECUENTE}% de descuento.")


def _then_volumen(f: dict) -> str:
    f["discount_pct"] += DESCUENTO_VOLUMEN
    return (f"Pedido de {f['units_total']} unidades "
            f"(≥{UNIDADES_PARA_VOLUMEN}): +{DESCUENTO_VOLUMEN}% por volumen.")


def _then_monto(f: dict) -> str:
    f["discount_pct"] += DESCUENTO_MONTO
    return (f"Subtotal de ${f['subtotal']:.0f} (≥${MONTO_PARA_DESCUENTO}): "
            f"+{DESCUENTO_MONTO}% por monto alto.")


def _then_tope(f: dict) -> str:
    f["discount_pct"] = DESCUENTO_MAXIMO
    return f"Descuento acumulado limitado al máximo de {DESCUENTO_MAXIMO}%."


def _then_no_registrado(f: dict) -> str:
    f["flags"]["registro_sugerido"] = True
    return ("Cliente no registrado: se sugiere registrarlo para acceder a "
            "beneficios de cliente frecuente.")


def _then_total(f: dict) -> str:
    desc = f["discount_pct"]
    f["discount_amount"] = round(f["subtotal"] * desc / 100, 2)
    f["total"] = round(f["subtotal"] - f["discount_amount"], 2)
    return (f"Total: ${f['subtotal']:.0f} − {desc:.0f}% "
            f"(${f['discount_amount']:.0f}) = ${f['total']:.0f}.")


# ----------------------------- Base de reglas -----------------------------
def build_order_rules() -> list[Rule]:
    """Devuelve la base de reglas IF/THEN para procesar un pedido."""
    return [
        Rule(
            name="reabastecimiento",
            description="SI hay ítems con stock insuficiente ENTONCES sugerir reabastecimiento",
            condition=lambda f: any(not it["available"] for it in f["items"]),
            action=_then_restock,
            priority=100,
        ),
        Rule(
            name="descuento_cliente_frecuente",
            description=f"SI el cliente es frecuente ENTONCES +{DESCUENTO_FRECUENTE}% de descuento",
            condition=lambda f: bool(f.get("customer") and f["customer"].get("is_frequent")),
            action=_then_frecuente,
            priority=80,
        ),
        Rule(
            name="descuento_volumen",
            description=f"SI se piden ≥{UNIDADES_PARA_VOLUMEN} unidades ENTONCES +{DESCUENTO_VOLUMEN}% por volumen",
            condition=lambda f: f.get("units_total", 0) >= UNIDADES_PARA_VOLUMEN,
            action=_then_volumen,
            priority=70,
        ),
        Rule(
            name="descuento_monto_alto",
            description=f"SI el subtotal ≥ ${MONTO_PARA_DESCUENTO} ENTONCES +{DESCUENTO_MONTO}% por monto",
            condition=lambda f: f.get("subtotal", 0) >= MONTO_PARA_DESCUENTO,
            action=_then_monto,
            priority=60,
        ),
        Rule(
            name="tope_descuento",
            description=f"SI el descuento supera {DESCUENTO_MAXIMO}% ENTONCES limitarlo a {DESCUENTO_MAXIMO}%",
            condition=lambda f: f.get("discount_pct", 0) > DESCUENTO_MAXIMO,
            action=_then_tope,
            priority=20,
        ),
        Rule(
            name="cliente_no_registrado",
            description="SI el cliente no está registrado ENTONCES invitar a registrarse",
            condition=lambda f: f.get("customer") is None,
            action=_then_no_registrado,
            priority=15,
        ),
        Rule(
            name="calculo_total",
            description="SIEMPRE calcular el total aplicando el descuento final",
            condition=lambda f: "subtotal" in f and "total" not in f,
            action=_then_total,
            priority=1,
        ),
    ]
