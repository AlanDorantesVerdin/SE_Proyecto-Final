"""
Datos de ejemplo para la tienda de películas físicas.

Ejecuta:
    python -m database.seed

Algunos títulos tienen stock 0 o muy bajo a propósito, para demostrar las
INFERENCIAS del Agente 2 (ej. "si stock < cantidad -> sugerir reabastecimiento").
Con `with_samples=True` también se cargan rentas de ejemplo (algunas vencidas)
para demostrar la inferencia de "rentas vencidas".
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from database.db import SCHEMA, get_connection

# (título, género, año, formato, precio_compra, precio_renta, stock, rating)
MOVIES = [
    ("The Matrix",        "Ciencia ficción", 1999, "Blu-ray", 149, 39,  8, 4.8),
    ("Titanic",           "Drama/Romance",   1997, "DVD",     129, 35,  5, 4.6),
    ("Jurassic Park",     "Aventura",        1993, "DVD",     119, 35,  3, 4.7),
    ("El Rey León",       "Animación",       1994, "Blu-ray", 139, 39, 10, 4.9),
    ("Pulp Fiction",      "Crimen",          1994, "DVD",     129, 35,  2, 4.8),
    ("Toy Story",         "Animación",       1995, "DVD",     119, 35,  6, 4.8),
    ("Terminator 2",      "Acción",          1991, "Blu-ray", 149, 39,  4, 4.7),
    ("Forrest Gump",      "Drama",           1994, "DVD",     129, 35,  0, 4.8),  # agotado
    ("Shrek",             "Animación",       2001, "DVD",     119, 35,  7, 4.6),
    ("El Padrino",        "Crimen",          1972, "4K",      199, 49,  3, 5.0),
    ("Volver al Futuro",  "Ciencia ficción", 1985, "Blu-ray", 139, 39,  5, 4.8),
    ("Gladiador",         "Acción",          2000, "Blu-ray", 149, 39,  1, 4.7),  # stock bajo
    # --- Ampliación del catálogo (más géneros) ---
    ("El Exorcista",      "Terror",          1973, "Blu-ray", 149, 39,  4, 4.6),
    ("El Resplandor",     "Terror",          1980, "Blu-ray", 149, 39,  3, 4.7),
    ("El Conjuro",        "Terror",          2013, "DVD",     129, 35,  0, 4.4),  # agotado
    ("Coco",              "Animación",       2017, "Blu-ray", 139, 39,  9, 4.9),
    ("Interestelar",      "Ciencia ficción", 2014, "4K",      189, 49,  6, 4.8),
    ("Parásito",          "Thriller",        2019, "Blu-ray", 159, 45,  5, 4.9),
    ("Spider-Man",        "Acción",          2002, "DVD",     119, 35,  7, 4.3),
    ("Avengers",          "Acción",          2012, "Blu-ray", 149, 39,  5, 4.5),
]

# (nombre, teléfono, es_frecuente, num_rentas)
CUSTOMERS = [
    ("Alan Dorantes", "+5216561234567", 1, 7),   # cliente frecuente
    ("María López",   "+5216567654321", 0, 1),
    ("Carlos Ruiz",   "+5216559876543", 0, 2),
    ("Sofía Méndez",  "+5216551112233", 1, 5),   # cliente frecuente
]

# Rentas de ejemplo: (teléfono, título, días_para_vencer)  negativo = vencida
SAMPLE_RENTALS = [
    ("+5216561234567", "Titanic", -5),   # Alan: vencida hace 5 días
    ("+5216561234567", "Shrek",    3),   # Alan: vigente
    ("+5216551112233", "Coco",    -2),   # Sofía: vencida hace 2 días
]


def _seed_sample_rentals(conn) -> None:
    """Inserta rentas de ejemplo (algunas vencidas) para las demostraciones."""
    for phone, title, days in SAMPLE_RENTALS:
        cust = conn.execute("SELECT id FROM customers WHERE phone = ?", (phone,)).fetchone()
        movie = conn.execute("SELECT id FROM movies WHERE title = ?", (title,)).fetchone()
        if not cust or not movie:
            continue
        due = (date.today() + timedelta(days=days)).isoformat()
        estado = "vencida" if days < 0 else "activa"
        conn.execute(
            "INSERT INTO rentals (customer_id, movie_id, due_date, status) "
            "VALUES (?, ?, ?, ?)",
            (cust["id"], movie["id"], due, estado),
        )


# Pedidos confirmados (historial): (teléfono, tipo, [(título, cant)], minutos_atrás)
DEMO_HISTORY = [
    ("+5216561234567", "renta",  [("The Matrix", 1), ("Interestelar", 1)],        35),
    ("+5216551112233", "compra", [("Coco", 1), ("El Rey León", 1)],                95),
    ("+5216559876543", "renta",  [("Pulp Fiction", 1)],                            140),
    ("+5216561234567", "compra", [("El Padrino", 1), ("Spider-Man", 1)],           210),
    ("+5216551112233", "renta",  [("Shrek", 2), ("Toy Story", 1)],                 280),
    ("+5216567654321", "renta",  [("Titanic", 1)],                                 360),
    ("+5216559876543", "compra", [("Avengers", 1)],                                430),
    ("+5216561234567", "renta",  [("Volver al Futuro", 1), ("Terminator 2", 1)],   520),
    ("+5216551112233", "compra", [("Interestelar", 1)],                            700),
    ("+5216567654321", "renta",  [("El Exorcista", 1)],                            900),
]

# Pedidos por validar (llegan del bot): (teléfono, tipo, [(título, cant, acción)], min)
DEMO_PENDING = [
    ("+5216561234567", "renta",  [("The Matrix", 1, "rentar"), ("Interestelar", 1, "rentar"),
                                  ("Spider-Man", 1, "rentar"), ("Avengers", 1, "rentar"),
                                  ("Coco", 1, "rentar")],                          6),
    ("+5216559876543", "compra", [("Forrest Gump", 1, "comprar"), ("Avengers", 1, "comprar")], 14),
    ("+5216551112233", "compra", [("El Padrino", 1, "comprar"), ("Interestelar", 1, "comprar")], 22),
    ("+5216567654321", "renta",  [("El Conjuro", 1, "rentar")],                    40),
    ("+5216561234567", "renta",  [("Gladiador", 1, "rentar"), ("Pulp Fiction", 1, "rentar")], 58),
]

# Reabastecimiento extra: (título, kind, sugerido, solicitudes, género|None)
DEMO_RESTOCK = [
    ("Forrest Gump", "agotado",     5, 4, None),
    ("El Conjuro",   "agotado",     4, 3, None),
    ("Gladiador",    "stock_bajo",  4, 2, None),
    ("Pulp Fiction", "stock_bajo",  3, 2, None),
    ("Wicked",          "titulo_nuevo", 3, 5, "Musical"),
    ("Gru 4",           "titulo_nuevo", 4, 7, "Animación"),
    ("Godzilla x Kong", "titulo_nuevo", 3, 4, "Acción"),
]


def _seed_demo_orders(conn) -> None:
    """Genera pedidos (historial + por validar) con totales reales del motor."""
    from core.business_rules import build_order_rules, make_order_facts
    from core.inference_engine import InferenceEngine

    engine = InferenceEngine(build_order_rules())
    movies = {r["title"]: dict(r) for r in conn.execute("SELECT * FROM movies").fetchall()}
    customers = {r["phone"]: dict(r) for r in conn.execute("SELECT * FROM customers").fetchall()}

    def insert(phone, tipo, lines, mins, status):
        cust = customers[phone]
        default_action = "rentar" if tipo == "renta" else "comprar"
        items = [{"title": t, "quantity": q, "action": (ln[2] if len(ln) > 2 else default_action),
                  "stock": movies[t]["stock"], "price_rent": movies[t]["price_rent"],
                  "price_buy": movies[t]["price_buy"]}
                 for ln in lines for t, q in [(ln[0], ln[1])]]
        facts = make_order_facts(cust, items)
        res = engine.run(facts)
        snap_items = [{"movie_id": movies[it["title"]]["id"], "title": it["title"],
                       "format": movies[it["title"]]["format"], "genre": movies[it["title"]]["genre"],
                       "quantity": it["quantity"], "action": it["action"],
                       "unit_price": it["unit_price"], "line_total": it["line_total"],
                       "stock": movies[it["title"]]["stock"], "available": it["available"]}
                      for it in facts["items"]]
        created = (datetime.now() - timedelta(minutes=mins)).isoformat()
        snap = {"customer_name": cust["name"], "phone": phone, "type": tipo, "channel": "whatsapp",
                "items": snap_items, "subtotal": facts["subtotal"],
                "discount_pct": facts["discount_pct"], "discount_amount": facts.get("discount_amount", 0),
                "total": facts.get("total", 0), "reasoning": [{"text": r} for r in res.reasoning],
                "needs_attention": any(not it["available"] for it in snap_items)}
        cur = conn.execute(
            "INSERT INTO orders (customer_id, type, total, status, channel, phone, details_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (cust["id"], tipo, facts.get("total", 0), status, "whatsapp", phone,
             json.dumps(snap, ensure_ascii=False), created))
        oid = cur.lastrowid
        for it in snap_items:
            if it["available"]:
                conn.execute("INSERT INTO order_items (order_id, movie_id, quantity, unit_price) "
                             "VALUES (?, ?, ?, ?)",
                             (oid, it["movie_id"], it["quantity"], it["unit_price"]))

    for phone, tipo, lines, mins in DEMO_HISTORY:
        insert(phone, tipo, lines, mins, "confirmado")
    for phone, tipo, lines, mins in DEMO_PENDING:
        insert(phone, tipo, lines, mins, "por_validar")


def _seed_restock(conn) -> None:
    """Carga sugerencias de reabastecimiento de ejemplo."""
    movies = {r["title"]: dict(r) for r in conn.execute("SELECT * FROM movies").fetchall()}
    for title, kind, qty, req, genre in DEMO_RESTOCK:
        m = movies.get(title)
        conn.execute(
            "INSERT INTO restock_suggestions (movie_id, title, suggested_qty, requests, kind, genre) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (m["id"] if m else None, title, qty, req, kind, m["genre"] if m else genre))


def seed(db_path: str | None = None, with_samples: bool = False) -> None:
    """
    Crea las tablas y carga el catálogo + clientes (idempotente).

    Si `with_samples` es True, también carga rentas de ejemplo (para demos).
    Los tests usan `with_samples=False` para partir de un estado limpio.
    """
    conn = get_connection(db_path)
    try:
        # Reinicio total: se eliminan y recrean las tablas para garantizar que
        # el esquema esté siempre actualizado (la base de datos es regenerable).
        for tabla in ("order_items", "rentals", "restock_suggestions",
                      "orders", "customers", "movies"):
            conn.execute(f"DROP TABLE IF EXISTS {tabla};")
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT INTO movies "
            "(title, genre, year, format, price_buy, price_rent, stock, rating) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            MOVIES,
        )
        for name, phone, freq, rentals in CUSTOMERS:
            conn.execute(
                "INSERT INTO customers (name, phone, is_frequent, rentals_count) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(phone) DO UPDATE SET "
                "  name = excluded.name, "
                "  is_frequent = excluded.is_frequent, "
                "  rentals_count = excluded.rentals_count",
                (name, phone, freq, rentals),
            )
        if with_samples:
            _seed_sample_rentals(conn)
            _seed_demo_orders(conn)
            _seed_restock(conn)
        conn.commit()
        extra = (f", {len(DEMO_HISTORY)} pedidos, {len(DEMO_PENDING)} por validar"
                 if with_samples else "")
        print(f"✓ Base de datos lista: {len(MOVIES)} películas, "
              f"{len(CUSTOMERS)} clientes{extra}.")
    finally:
        conn.close()


if __name__ == "__main__":
    from dotenv import load_dotenv

    from core.console import enable_utf8

    enable_utf8()
    load_dotenv()
    seed(with_samples=True)
