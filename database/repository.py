"""
Consultas de acceso a datos (repository pattern).

Centraliza el SQL para que los agentes no escriban consultas directamente.
"""
from __future__ import annotations

import sqlite3

from database.db import get_connection


def list_movies(db_path: str | None = None) -> list[sqlite3.Row]:
    """Devuelve todo el catálogo ordenado por título."""
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT * FROM movies ORDER BY title").fetchall()
    finally:
        conn.close()


def count_movies(db_path: str | None = None) -> int:
    """Cuenta cuántas películas hay en el catálogo."""
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT COUNT(*) AS n FROM movies").fetchone()["n"]
    finally:
        conn.close()


def find_movies_by_title(query: str, db_path: str | None = None) -> list[sqlite3.Row]:
    """Busca películas cuyo título contenga `query` (sin distinguir mayúsculas)."""
    query = (query or "").strip()
    if not query:
        return []
    conn = get_connection(db_path)
    try:
        like = f"%{query}%"
        return conn.execute(
            "SELECT * FROM movies WHERE title LIKE ? COLLATE NOCASE "
            "ORDER BY stock DESC",
            (like,),
        ).fetchall()
    finally:
        conn.close()


def get_customer_by_phone(phone: str | None,
                          db_path: str | None = None) -> sqlite3.Row | None:
    """Identifica a un cliente por su número de teléfono (WhatsApp)."""
    if not phone:
        return None
    conn = get_connection(db_path)
    try:
        return conn.execute(
            "SELECT * FROM customers WHERE phone = ?", (phone,)
        ).fetchone()
    finally:
        conn.close()
