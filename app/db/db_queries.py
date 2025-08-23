import logging
from db_utils import execute_query


def get_cards_by_name_substring(substring, limit=None, offset=None):
    """Return rows whose name contains the substring (case-insensitive)."""
    base_sql = """
        SELECT id, local_id, name, mcm_meta_id, card_text, color, mana_cost,
               converted_mana_cost, card_type, card_subtype, card_supertype, power, toughness
        FROM cards
        WHERE name ILIKE %s
    """
    params = [f"%{substring}%"]

    if isinstance(limit, int):
        base_sql += " LIMIT %s"
        params.append(limit)
    if isinstance(offset, int):
        base_sql += " OFFSET %s"
        params.append(offset)

    try:
        return execute_query(base_sql, tuple(params), fetch=True)
    except Exception as e:
        logging.error(f"Query failed: {e}")
        return []