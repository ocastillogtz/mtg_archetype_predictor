import logging
import psycopg2

def create_card_history_table(conn):
    """
    Creates a table to store the history of card-related actions.

    Fields:
        id: SERIAL PRIMARY KEY (auto-increment)
        card_id: INTEGER NOT NULL (references a card). This is called local id in the card table
        action: TEXT NOT NULL (describes the action taken, e.g., 'created', 'updated', 'deleted')
        attribute_that_changed: TEXT (the name of the attribute that was modified)
        previous_value: TEXT (the old value before change)
        new_value: TEXT (the new value after change)
        timestamp: TIMESTAMP DEFAULT CURRENT_TIMESTAMP (automatically records the time of the action)

    :param conn: A psycopg2 connection object
    :return: True if successful, False otherwise
    """
    try:
        cur = conn.cursor()

        # Create the card_history table
        cur.execute("""
            CREATE TABLE card_history (
                id SERIAL PRIMARY KEY,
                card_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                attribute_that_changed TEXT,
                previous_value TEXT,
                new_value TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        logging.info("Successfully created the card_history table.")
        cur.close()
        return True

    except (psycopg2.DatabaseError, Exception) as error_message:
        logging.error(error_message)
        return False


def add_card_history_entry(conn, card_id, action, attribute_that_changed=None, previous_value=None, new_value=None):
    """
    Inserts a new entry into the card_history table.

    :param conn: psycopg2 connection object
    :param card_id: int, ID of the card
    :param action: str, description of the action (e.g., 'created', 'updated', 'deleted')
    :param attribute_that_changed: str or None, name of the attribute that changed
    :param previous_value: str or None, value before the change
    :param new_value: str or None, value after the change
    :return: True if successful, False otherwise
    """
    try:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO card_history (card_id, action, attribute_that_changed, previous_value, new_value)
            VALUES (%s, %s, %s, %s, %s)
        """, (card_id, action, attribute_that_changed, previous_value, new_value))

        conn.commit()
        logging.info("Successfully inserted a new card history entry.")
        cur.close()
        return True

    except (psycopg2.DatabaseError, Exception) as error_message:
        logging.error(error_message)
        return False


def get_last_card_history_entries(conn, card_id, number_of_last_entries):
    """
    Retrieves the last X entries for a given card_id from the card_history table.

    :param conn: psycopg2 connection object
    :param card_id: int, ID of the card
    :param number_of_last_entries: int, number of entries to retrieve
    :return: List of tuples representing the rows, or empty list if none found
    """
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT id, card_id, action, attribute_that_changed, previous_value, new_value, timestamp
            FROM card_history
            WHERE card_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (card_id, number_of_last_entries))

        rows = cur.fetchall()
        cur.close()
        return rows

    except (psycopg2.DatabaseError, Exception) as error_message:
        logging.error(error_message)
        return []