import logging
import pickle
import psycopg2
from psycopg2.extras import execute_values
from .db_utils import execute_query, bulk_insert_values, commit, rollback


# =============================
# Create table (runs once)
# =============================
def create_cards_table(conn):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY,
        mtg_arena_id INTEGER,
        name TEXT NOT NULL,
        color TEXT[],
        mana_cost TEXT,
        converted_mana_cost INTEGER,
        card_type TEXT[],
        subtypes TEXT[],
        super_types TEXT[],
        card_text TEXT,
        power INTEGER,
        toughness INTEGER,
        mcm_meta_id INTEGER,
        card_market_link TEXT,
        tcg_player_link TEXT,
        predicted_archetypes TEXT[],
        annotated_archetypes TEXT[],
        gold_standard_archetypes TEXT[],
        display_html TEXT,
        magic_card_object BYTEA
    );
    """

    try:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
            conn.commit()
            logging.info("Cards table created successfully.")

    except psycopg2.Error as e:
        print(f"Database error creating table: {e}")
        conn.rollback()
        conn.close()
        raise

# =============================
# Insert a single card
# =============================
def insert_magic_card(card):
    try:
        serialized_card = pickle.dumps(card)

        query = """
        INSERT INTO cards (
            id, mtg_arena_id, name, color, mana_cost, converted_mana_cost, card_type, subtypes, super_types,
            card_text, power, toughness, mcm_meta_id, card_market_link, tcg_player_link,
            predicted_archetypes, annotated_archetypes, gold_standard_archetypes,
            display_html, magic_card_object
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """

        params = (
            card.id,
            getattr(card, "mtg_arena_id", 0),
            card.name,
            card.color,
            card.mana_cost,
            card.converted_mana_cost,
            card.card_type,
            card.subtypes,
            card.super_types,
            card.card_text,
            card.power,
            card.toughness,
            card.mcm_meta_id,
            card.card_market_link,
            card.tcg_player_link,
            card.predicted_archetypes,
            card.annotated_archetypes,
            card.gold_standard_archetypes,
            card.display_html,
            serialized_card
        )

        execute_query(query, params)
        commit()
        logging.info(f"Inserted card: {card.name}")
    except Exception as e:
        rollback()
        logging.error(f"Failed to insert card {card.name}: {e}")
        raise

# =============================
# Bulk insert (fast)
# =============================

def insert_magic_cards_bulk(config, cards):
    """
    Insert a list of MagicCard objects into the database in bulk.
    Opens and closes its own connection (used for initialization).
    """
    conn = None
    try:
        dbname = config["postgresql"]["database"]
        host = config["postgresql"]["host"]
        port = config["postgresql"]["port"]
        user = config["database_user"]["user"]
        password = config["database_user"]["password"]
        conn = psycopg2.connect(dbname=dbname,
                              user=user,
                              password=password,
                              host=host,
                              port=port)
        with conn.cursor() as cur:
            rows = []
            for card in cards:
                serialized_card = pickle.dumps(card)
                rows.append((
                    card.id,
                    getattr(card, "mtg_arena_id", 0),
                    card.name,
                    card.color,
                    card.mana_cost,
                    card.converted_mana_cost,
                    card.card_type,
                    card.subtypes,
                    card.super_types,
                    card.card_text,
                    card.power,
                    card.toughness,
                    card.mcm_meta_id,
                    card.card_market_link,
                    card.tcg_player_link,
                    card.predicted_archetypes,
                    card.annotated_archetypes,
                    card.gold_standard_archetypes,
                    card.display_html,
                    serialized_card
                ))

            insert_sql = """
            INSERT INTO cards (
                id, mtg_arena_id, name, color, mana_cost, converted_mana_cost, card_type, subtypes, super_types,
                card_text, power, toughness, mcm_meta_id, card_market_link, tcg_player_link,
                predicted_archetypes, annotated_archetypes, gold_standard_archetypes,
                display_html, magic_card_object
            ) VALUES %s
            ON CONFLICT (id) DO NOTHING;
            """

            execute_values(cur, insert_sql, rows)
        conn.commit()
        logging.info(f"Successfully inserted {len(cards)} cards in bulk.")
    except Exception as e:
        logging.error(f"Bulk insert failed: {e}")
        if conn:
            try:
                conn.rollback()
            except Exception:
                logging.error("Rollback failed.")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                logging.error("Failed to close connection.")


# =============================
# Retrieve a single card by ID
# =============================
def get_magic_card(card_id):
    try:
        query = "SELECT magic_card_object FROM cards WHERE id = %s"
        rows = execute_query(query, (card_id,), fetch=True)
        if rows and rows[0][0]:
            return pickle.loads(rows[0][0])
        return None
    except Exception as e:
        logging.error(f"Failed to retrieve card {card_id}: {e}")
        return "<div><p>Query Failed</p></div>"

# =============================
# Search cards by name (partial match)
# Does NOT return magic_card_object or display_html
# =============================
def search_cards_by_name(partial_name):
    try:
        query = """
        SELECT id, mtg_arena_id, name, color, mana_cost, converted_mana_cost, card_type, subtypes, super_types,
               card_text, power, toughness, mcm_meta_id, card_market_link, tcg_player_link,
               predicted_archetypes, annotated_archetypes, gold_standard_archetypes
        FROM cards
        WHERE name ILIKE %s
        """
        rows = execute_query(query, (f"%{partial_name}%",), fetch=True)
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "mtg_arena_id": row[1],
                "name": row[2],
                "color": row[3],
                "mana_cost": row[4],
                "converted_mana_cost": row[5],
                "card_type": row[6],
                "subtypes": row[7],
                "super_types": row[8],
                "card_text": row[9],
                "power": row[10],
                "toughness": row[11],
                "mcm_meta_id": row[12],
                "card_market_link": row[13],
                "tcg_player_link": row[14],
                "predicted_archetypes": row[15],
                "annotated_archetypes": row[16],
                "gold_standard_archetypes": row[17]
            })
        return result
    except Exception as e:
        logging.error(f"Failed to search cards with name like {partial_name}: {e}")
        raise

# =============================
# Update an existing card
# =============================
def update_magic_card(card):
    try:
        serialized_card = pickle.dumps(card)
        query = """
        UPDATE cards
        SET mtg_arena_id = %s,
            name = %s,
            color = %s,
            mana_cost = %s,
            converted_mana_cost = %s,
            card_type = %s,
            subtypes = %s,
            super_types = %s,
            card_text = %s,
            power = %s,
            toughness = %s,
            mcm_meta_id = %s,
            card_market_link = %s,
            tcg_player_link = %s,
            predicted_archetypes = %s,
            annotated_archetypes = %s,
            gold_standard_archetypes = %s,
            display_html = %s,
            magic_card_object = %s
        WHERE id = %s
        """
        params = (
            getattr(card, "mtg_arena_id", None),
            card.name,
            card.color,
            card.mana_cost,
            card.converted_mana_cost,
            card.card_type,
            card.subtypes,
            card.super_types,
            card.card_text,
            card.power,
            card.toughness,
            card.mcm_meta_id,
            card.card_market_link,
            card.tcg_player_link,
            card.predicted_archetypes,
            card.annotated_archetypes,
            card.gold_standard_archetypes,
            card.display_html,
            serialized_card,
            card.id
        )
        execute_query(query, params)
        commit()
        logging.info(f"Updated card: {card.name}")
    except Exception as e:
        rollback()
        logging.error(f"Failed to update card {card.name}: {e}")
        raise

# =============================
# Delete a card by ID
# =============================
def delete_magic_card(card_id):
    try:
        query = "DELETE FROM cards WHERE id = %s"
        execute_query(query, (card_id,))
        commit()
        logging.info(f"Deleted card with ID: {card_id}")
    except Exception as e:
        rollback()
        logging.error(f"Failed to delete card {card_id}: {e}")
        raise
