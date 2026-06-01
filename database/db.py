"""
Conexión y esquema de la base de datos SQLite.

El archivo .db NO se versiona en Git (ver .gitignore); se regenera en
cualquier momento con `python -m database.seed`.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# Esquema de la tienda de películas físicas (estilo Blockbuster moderno).
SCHEMA = """
CREATE TABLE IF NOT EXISTS movies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    genre       TEXT,
    year        INTEGER,
    format      TEXT    DEFAULT 'DVD',          -- DVD | Blu-ray | 4K
    price_buy   REAL    NOT NULL,
    price_rent  REAL    NOT NULL,
    stock       INTEGER NOT NULL DEFAULT 0,
    rating      REAL    DEFAULT 0
);

CREATE TABLE IF NOT EXISTS customers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT,
    phone         TEXT UNIQUE,
    is_frequent   INTEGER DEFAULT 0,             -- 0 / 1
    rentals_count INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Tablas usadas por el Agente 2 (Generador de Pedido) en etapas posteriores.
CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER REFERENCES customers(id),
    type        TEXT,                            -- compra | renta
    total       REAL DEFAULT 0,
    status      TEXT DEFAULT 'pendiente',
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER REFERENCES orders(id),
    movie_id    INTEGER REFERENCES movies(id),
    quantity    INTEGER NOT NULL,
    unit_price  REAL NOT NULL
);
"""


def resolve_db_path(db_path: str | None = None) -> str:
    """Ruta del archivo .db (configurable por la variable DATABASE_PATH)."""
    return db_path or os.getenv("DATABASE_PATH", "database/store.db")


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Abre una conexión SQLite con claves foráneas y filas tipo dict."""
    path = resolve_db_path(db_path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row          # acceso por nombre de columna
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str | None = None) -> None:
    """Crea las tablas si no existen."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
