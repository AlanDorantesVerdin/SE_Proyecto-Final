"""
Datos de ejemplo para la tienda de películas físicas.

Ejecuta:
    python -m database.seed

Algunos títulos tienen stock 0 o stock muy bajo a propósito, para poder
demostrar las INFERENCIAS del Agente 2 (ej. "si stock < cantidad -> sugerir
reabastecimiento").
"""
from __future__ import annotations

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
]

# (nombre, teléfono, es_frecuente, num_rentas)
CUSTOMERS = [
    ("Alan Dorantes", "+5216561234567", 1, 7),   # cliente frecuente
    ("María López",   "+5216567654321", 0, 1),
]


def seed(db_path: str | None = None) -> None:
    """Crea las tablas y carga el catálogo + clientes de ejemplo (idempotente)."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
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
        conn.commit()
        print(f"✓ Base de datos lista: {len(MOVIES)} películas, "
              f"{len(CUSTOMERS)} clientes.")
    finally:
        conn.close()


if __name__ == "__main__":
    from dotenv import load_dotenv

    from core.console import enable_utf8

    enable_utf8()
    load_dotenv()
    seed()
