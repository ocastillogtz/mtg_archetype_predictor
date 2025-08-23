import logging
from db_utils import execute_query, commit

ALLOWED_TABLES = {"cards"}
# Optionally, whitelist columns per table to avoid SQL injection via identifiers
ALLOWED_COLUMNS = {
    "cards": {
        "name", "mcm_meta_id", "card_text", "automatically_annotated", "manually_annotated",
        "gold_standard", "converted_mana_cost", "color", "mana_cost", "card_type",
        "card_subtype", "card_supertype", "power", "toughness"
    }
}


def update_row(table, where_col, where_val, updates: dict):
    """Generic, safe UPDATE with identifier whitelisting and value parameterization."""
    if table not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")
    for col in [where_col, *updates.keys()]:
        if col not in ALLOWED_COLUMNS[table]:
            raise ValueError(f"Invalid column name: {col}")

    set_clause = ", ".join([f"{col} = %s" for col in updates.keys()])
    sql = f"UPDATE {table} SET {set_clause} WHERE {where_col} = %s"
    params = list(updates.values()) + [where_val]

    logging.info(f"Updating {table} WHERE {where_col} = {where_val}")
    execute_query(sql, tuple(params))
    commit()


# Convenience wrapper specifically for cards using local_id as the key

def update_card_by_local_id(local_id: int, updates: dict):
    return update_row("cards", "local_id", local_id, updates)