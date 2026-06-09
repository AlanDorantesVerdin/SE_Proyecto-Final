"""
Consultas de acceso a datos (repository pattern).

Centraliza el SQL para que los agentes no escriban consultas directamente.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

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


# ===== Escritura / persistencia de pedidos (Agente 2, Día 4) =====

def get_movie_by_title(title: str, db_path: str | None = None) -> sqlite3.Row | None:
    """Busca una película por título exacto (sin distinguir mayúsculas)."""
    conn = get_connection(db_path)
    try:
        return conn.execute(
            "SELECT * FROM movies WHERE title = ? COLLATE NOCASE", (title,)
        ).fetchone()
    finally:
        conn.close()


def ensure_customer(phone: str | None, name: str | None = None,
                    db_path: str | None = None) -> int | None:
    """Devuelve el id del cliente; si no existe, lo registra (cliente nuevo)."""
    if not phone:
        return None
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT id FROM customers WHERE phone = ?", (phone,)).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO customers (name, phone) VALUES (?, ?)", (name or phone, phone)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def persist_order(*, customer_id: int | None, tipo: str, order,
                  due_days: int = 3, frequent_threshold: int = 3,
                  db_path: str | None = None) -> int:
    """
    Guarda un pedido completo en UNA sola transacción y devuelve su id.

    - Inserta el pedido y sus líneas disponibles.
    - Descuenta el stock de cada película comprada/rentada.
    - Crea una renta (con fecha de vencimiento) por cada línea rentada.
    - Registra una sugerencia de reabastecimiento por cada línea agotada.
    - Actualiza el conteo de rentas del cliente y lo marca como frecuente
      al alcanzar el umbral.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO orders (customer_id, type, total, status) VALUES (?, ?, ?, ?)",
            (customer_id, tipo, order.total, "confirmado"),
        )
        order_id = cur.lastrowid
        rented_units = 0

        for ln in order.lines:
            movie = conn.execute(
                "SELECT id, stock FROM movies WHERE title = ? COLLATE NOCASE", (ln.title,)
            ).fetchone()
            if not movie:
                continue

            if ln.available:
                conn.execute(
                    "INSERT INTO order_items (order_id, movie_id, quantity, unit_price) "
                    "VALUES (?, ?, ?, ?)",
                    (order_id, movie["id"], ln.quantity, ln.unit_price),
                )
                conn.execute(
                    "UPDATE movies SET stock = MAX(0, stock - ?) WHERE id = ?",
                    (ln.quantity, movie["id"]),
                )
                if ln.action == "rentar":
                    due = (date.today() + timedelta(days=due_days)).isoformat()
                    conn.execute(
                        "INSERT INTO rentals (customer_id, movie_id, order_id, due_date) "
                        "VALUES (?, ?, ?, ?)",
                        (customer_id, movie["id"], order_id, due),
                    )
                    rented_units += ln.quantity
            else:
                faltan = max(1, ln.quantity - movie["stock"])
                conn.execute(
                    "INSERT INTO restock_suggestions (movie_id, title, suggested_qty) "
                    "VALUES (?, ?, ?)",
                    (movie["id"], ln.title, faltan),
                )

        if customer_id and rented_units:
            conn.execute(
                "UPDATE customers SET rentals_count = rentals_count + ? WHERE id = ?",
                (rented_units, customer_id),
            )
            conn.execute(
                "UPDATE customers SET is_frequent = 1 WHERE id = ? AND rentals_count >= ?",
                (customer_id, frequent_threshold),
            )

        conn.commit()
        return order_id
    finally:
        conn.close()


def get_order(order_id: int, db_path: str | None = None):
    """Devuelve (pedido, líneas) para inspección/explicación."""
    conn = get_connection(db_path)
    try:
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        items = conn.execute(
            "SELECT oi.*, m.title FROM order_items oi "
            "JOIN movies m ON m.id = oi.movie_id WHERE order_id = ?",
            (order_id,),
        ).fetchall()
        return order, items
    finally:
        conn.close()


def list_rentals(db_path: str | None = None) -> list[sqlite3.Row]:
    """Lista las rentas con el título de la película."""
    conn = get_connection(db_path)
    try:
        return conn.execute(
            "SELECT r.*, m.title FROM rentals r JOIN movies m ON m.id = r.movie_id "
            "ORDER BY r.id"
        ).fetchall()
    finally:
        conn.close()


def list_restock(db_path: str | None = None) -> list[sqlite3.Row]:
    """Lista las sugerencias de reabastecimiento pendientes."""
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT * FROM restock_suggestions ORDER BY id").fetchall()
    finally:
        conn.close()


def count_orders(db_path: str | None = None) -> int:
    """Cuenta cuántos pedidos hay guardados."""
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"]
    finally:
        conn.close()


def count_overdue_rentals(customer_id: int | None, db_path: str | None = None) -> int:
    """Cuenta las rentas vencidas (sin devolver) de un cliente."""
    if not customer_id:
        return 0
    today = date.today().isoformat()
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM rentals "
            "WHERE customer_id = ? AND returned_at IS NULL AND due_date < ?",
            (customer_id, today),
        ).fetchone()
        return row["n"]
    finally:
        conn.close()


def list_overdue_rentals(customer_id: int | None = None,
                         db_path: str | None = None) -> list[sqlite3.Row]:
    """Lista las rentas vencidas (de un cliente o de todos)."""
    today = date.today().isoformat()
    conn = get_connection(db_path)
    try:
        query = (
            "SELECT r.*, m.title, c.name AS customer_name "
            "FROM rentals r "
            "JOIN movies m ON m.id = r.movie_id "
            "JOIN customers c ON c.id = r.customer_id "
            "WHERE r.returned_at IS NULL AND r.due_date < ? "
        )
        params: list = [today]
        if customer_id:
            query += "AND r.customer_id = ? "
            params.append(customer_id)
        query += "ORDER BY r.due_date"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()
