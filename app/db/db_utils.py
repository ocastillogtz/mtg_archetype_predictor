import logging
from flask import g, current_app
from psycopg2.extras import execute_values

# Acquire and return pooled connections via Flask's app context

def get_db_connection():
    if 'db_conn' not in g:
        g.db_conn = current_app.config['DB_POOL'].getconn()
    return g.db_conn


def return_db_connection():
    db_conn = g.pop('db_conn', None)
    if db_conn:
        current_app.config['DB_POOL'].putconn(db_conn)


# Core helpers

def execute_query(query, params=None, fetch=False):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
    except Exception as e:
        logging.error(f"Query failed: {e}\nSQL: {query}\nParams: {params}")
        try:
            conn.rollback()
        except Exception:
            pass
        raise


def bulk_insert_values(insert_sql_values_placeholder, rows):
    """
    Execute a bulk insert using psycopg2.extras.execute_values.

    Example usage:
        insert_sql_values_placeholder = \"""
            INSERT INTO cards (local_id, name, mcm_meta_id, card_object,
                               converted_mana_cost, color, mana_cost, card_type,
                               card_subtype, card_supertype, card_text, power, toughness)
            VALUES %s
        \"""
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            execute_values(cur, insert_sql_values_placeholder, rows)
    except Exception as e:
        logging.error(f"Bulk insert failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        raise


def commit():
    get_db_connection().commit()


def rollback():
    get_db_connection().rollback()