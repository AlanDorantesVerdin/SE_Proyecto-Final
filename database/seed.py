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

from datetime import date, timedelta

from database.db import get_connection, init_db

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


def seed(db_path: str | None = None, with_samples: bool = False) -> None:
    """
    Crea las tablas y carga el catálogo + clientes (idempotente).

    Si `with_samples` es True, también carga rentas de ejemplo (para demos).
    Los tests usan `with_samples=False` para partir de un estado limpio.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        # Limpiar transacciones para un estado de demostración consistente
        # (además, las claves foráneas impiden borrar películas con pedidos).
        for tabla in ("order_items", "rentals", "restock_suggestions", "orders"):
            conn.execute(f"DELETE FROM {tabla};")
        conn.execute("DELETE FROM movies;")
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
        conn.commit()
        extra = f", {len(SAMPLE_RENTALS)} rentas de ejemplo" if with_samples else ""
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
