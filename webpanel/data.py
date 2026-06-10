"""
Generador de datos del panel REBOBINA a partir de la base de datos REAL.

Produce un diccionario con la MISMA forma que el `window.STORE_DATA` del
prototipo de diseño, para que el front-end (React) se reutilice tal cual,
pero alimentado con los datos vivos de SQLite (películas, clientes, pedidos,
rentas, reabastecimiento e inferencias).
"""
from __future__ import annotations

import json
from datetime import date, datetime

from core import business_rules as BR
from database.db import get_connection


def _iso(ts) -> str:
    return str(ts).replace(" ", "T") if ts else ""


def _mins_ago(ts, now: datetime) -> int:
    try:
        clean = str(ts).replace(" ", "T").replace("Z", "")
        return max(0, int((now - datetime.fromisoformat(clean)).total_seconds() // 60))
    except (ValueError, TypeError):
        return 0


def _order_from_row(row) -> dict:
    """Reconstruye un pedido a partir del snapshot JSON guardado."""
    snap = json.loads(row["details_json"]) if row["details_json"] else {}
    d = dict(snap)
    d["id"] = row["id"]
    d["customer_id"] = row["customer_id"]
    d["status"] = row["status"]
    d["created_at"] = _iso(row["created_at"])
    d.setdefault("channel", row["channel"] or "whatsapp")
    d.setdefault("phone", row["phone"])
    d.setdefault("customer_name", "Cliente")
    d.setdefault("type", row["type"] or "compra")
    d.setdefault("items", [])
    d.setdefault("total", row["total"] or 0)
    d.setdefault("subtotal", d.get("total", 0))
    d.setdefault("discount_pct", 0)
    d.setdefault("discount_amount", 0)
    d.setdefault("reasoning", [])
    d.setdefault("flags", [])
    d.setdefault("needs_attention", False)
    return d


def _discount_rules() -> list[dict]:
    return [
        {"id": "frecuente", "name": "Cliente frecuente", "pct": BR.DESCUENTO_FRECUENTE,
         "priority": 80, "criteria": "El cliente está marcado como frecuente.",
         "cond": "is_frequent = 1", "applies": "Clientes con 3 o más rentas."},
        {"id": "volumen", "name": "Compra por volumen", "pct": BR.DESCUENTO_VOLUMEN,
         "priority": 70, "criteria": f"El pedido suma {BR.UNIDADES_PARA_VOLUMEN} o más unidades.",
         "cond": f"unidades ≥ {BR.UNIDADES_PARA_VOLUMEN}", "applies": "Cualquier cliente."},
        {"id": "monto", "name": "Monto alto", "pct": BR.DESCUENTO_MONTO,
         "priority": 60, "criteria": f"El subtotal alcanza o supera ${BR.MONTO_PARA_DESCUENTO}.",
         "cond": f"subtotal ≥ ${BR.MONTO_PARA_DESCUENTO}", "applies": "Tickets altos."},
        {"id": "vencidas", "name": "Aviso por rentas vencidas", "pct": 0,
         "priority": 90, "criteria": "El cliente tiene rentas sin devolver.",
         "cond": "vencidas > 0", "applies": "Se avisa antes de una nueva renta."},
        {"id": "tope", "name": "Tope de descuento", "pct": BR.DESCUENTO_MAXIMO,
         "priority": 20, "criteria": "Los descuentos se acumulan, pero no superan el tope.",
         "cond": f"descuento ≤ {BR.DESCUENTO_MAXIMO}%", "applies": "Límite de seguridad."},
    ]


def build_store_data(db_path: str | None = None) -> dict:
    """Construye el STORE_DATA del panel desde la base de datos."""
    conn = get_connection(db_path)
    try:
        now = datetime.now()
        today = date.today().isoformat()

        # ---- Catálogo ----
        def demand(rating):
            return "alta" if rating >= 4.7 else "media" if rating >= 4.4 else "baja"
        movies = [
            {"id": r["id"], "title": r["title"], "genre": r["genre"], "year": r["year"],
             "format": r["format"], "price_buy": r["price_buy"], "price_rent": r["price_rent"],
             "stock": r["stock"], "rating": r["rating"], "demand": demand(r["rating"])}
            for r in conn.execute("SELECT * FROM movies ORDER BY title")
        ]

        # ---- Clientes (+ gasto histórico) ----
        spend = {row["cid"]: row["s"] for row in conn.execute(
            "SELECT customer_id cid, COALESCE(SUM(total), 0) s FROM orders "
            "WHERE status = 'confirmado' GROUP BY customer_id")}
        customers = [
            {"id": r["id"], "name": r["name"], "phone": r["phone"],
             "is_frequent": r["is_frequent"], "rentals_count": r["rentals_count"],
             "created_at": _iso(r["created_at"]), "total_spend": spend.get(r["id"], 0)}
            for r in conn.execute("SELECT * FROM customers ORDER BY id")
        ]

        # ---- Pedidos ----
        orders = [_order_from_row(r) for r in conn.execute(
            "SELECT * FROM orders WHERE status = 'confirmado' ORDER BY id DESC")]
        pending = [_order_from_row(r) for r in conn.execute(
            "SELECT * FROM orders WHERE status = 'por_validar' ORDER BY id DESC")]

        # ---- Rentas ----
        rentals = []
        for r in conn.execute(
                "SELECT r.*, m.title, m.format, c.name cn FROM rentals r "
                "JOIN movies m ON m.id = r.movie_id JOIN customers c ON c.id = r.customer_id "
                "ORDER BY r.id"):
            overdue = r["returned_at"] is None and str(r["due_date"]) < today
            rentals.append({
                "id": r["id"], "customer_id": r["customer_id"], "customer_name": r["cn"],
                "movie_id": r["movie_id"], "title": r["title"], "format": r["format"],
                "rented_at": _iso(r["rented_at"]), "due_date": _iso(r["due_date"]),
                "status": "vencida" if overdue else (r["status"] or "activa")})

        # ---- Reabastecimiento ----
        restock = [
            {"id": r["id"], "movie_id": r["movie_id"], "title": r["title"],
             "type": r["kind"], "suggested_qty": r["suggested_qty"], "requests": r["requests"],
             "status": r["status"], "created_at": _iso(r["created_at"]),
             "format": r["mf"] or "—", "genre": r["genre"] or r["mg"]}
            for r in conn.execute(
                "SELECT s.*, m.format mf, m.genre mg FROM restock_suggestions s "
                "LEFT JOIN movies m ON m.id = s.movie_id ORDER BY s.id")
        ]

        # ---- Derivados / KPIs ----
        out_of_stock = [m for m in movies if m["stock"] == 0]
        low_stock = [m for m in movies if 0 < m["stock"] <= 2]
        overdue_r = [r for r in rentals if r["status"] == "vencida"]
        active_r = [r for r in rentals if r["status"] == "activa"]
        today_orders = [o for o in orders if _mins_ago(o["created_at"], now) < 1440]
        derived = {
            "lowStock": low_stock, "outOfStock": out_of_stock,
            "overdue": overdue_r, "activeRentals": active_r,
            "revenueToday": sum(o["total"] for o in today_orders),
            "ordersToday": len(today_orders),
            "pendingCount": len(pending),
            "attentionCount": sum(1 for p in pending if p.get("needs_attention")),
            "restockPending": sum(1 for r in restock if r["status"] == "pendiente"),
            "newTitleRequests": sum(1 for r in restock
                                    if r["type"] == "titulo_nuevo" and r["status"] == "pendiente"),
            "frequentCount": sum(1 for c in customers if c["is_frequent"]),
            "catalogValue": sum(m["price_buy"] * m["stock"] for m in movies),
            "totalStock": sum(m["stock"] for m in movies),
        }

        # ---- Actividad del bot (derivada) ----
        activity = []
        for p in pending[:5]:
            activity.append({"kind": "pedido", "minsAgo": _mins_ago(p["created_at"], now),
                             "text": f"Nuevo pedido de {p['type']} de {p['customer_name']} "
                                     f"({len(p['items'])} títulos)", "ref": p["id"]})
        for o in orders[:4]:
            verbo = "Renta" if o["type"] == "renta" else "Venta"
            activity.append({"kind": "venta", "minsAgo": _mins_ago(o["created_at"], now),
                             "text": f"{verbo} confirmada #{o['id']} — {o['customer_name']} "
                                     f"(${int(o['total'])})", "ref": o["id"]})
        for r in overdue_r[:2]:
            activity.append({"kind": "alerta", "minsAgo": _mins_ago(r["rented_at"], now),
                             "text": f"Renta vencida: {r['title']} — {r['customer_name']}", "ref": r["id"]})
        for r in [x for x in restock if x["type"] == "titulo_nuevo"][:2]:
            activity.append({"kind": "consulta", "minsAgo": _mins_ago(r["created_at"], now),
                             "text": f"Solicitud de título nuevo: «{r['title']}»", "ref": r["id"]})
        activity.sort(key=lambda a: a["minsAgo"])
        for i, a in enumerate(activity):
            a["id"] = i + 1

        return {
            "TODAY": now.isoformat(),
            "movies": movies, "customers": customers,
            "orders": orders, "pendingOrders": pending,
            "rentals": rentals, "restock": restock,
            "activity": activity, "discountRules": _discount_rules(),
            "derived": derived,
        }
    finally:
        conn.close()
