import bcrypt
import psycopg2
import logging
from app.db.db_utils import get_db_connection

def create_users_table(conn):
    """
    Creates the users table if it doesn't exist.
    Columns: id, username, hashed_password, salt, admin, active, created_date
    """
    create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL,
            salt TEXT NOT NULL,
            admin BOOLEAN NOT NULL DEFAULT FALSE,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """
    try:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
            conn.commit()
            logging.info("Succesfully created the user table")
    except psycopg2.Error as e:
        print(f"Database error creating table: {e}")
        conn.rollback()
        conn.close()



def create_user(conn, username, raw_password, admin=False):
    """
    Inserts a new user into the users table with a unique salt and returns the user ID.
    """
    try:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), salt)

        insert_query = """
            INSERT INTO users (username, hashed_password, salt, admin)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """
        with conn.cursor() as cursor:
            cursor.execute(insert_query, (
                username,
                hashed_password.decode('utf-8'),
                salt.decode('utf-8'),
                admin
            ))
            user_id = cursor.fetchone()[0]
            conn.commit()
            return user_id
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def authenticate_user(conn, username, raw_password):
    """
    Authenticates a user by username and password. Returns True if valid.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT hashed_password, active FROM users WHERE username = %s",
                (username,)
            )
            row = cur.fetchone()
            if row:
                hashed_password_db, active = row
                if not active:
                    return False  # inactive users cannot login
                if bcrypt.checkpw(raw_password.encode('utf-8'), hashed_password_db.encode('utf-8')):
                    return True
        return False
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def delete_user(conn, user_id):
    """
    Deletes a user from the users table by ID.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Database error deleting user: {e}")
        conn.rollback()
        return False


def disable_user(conn, user_id):
    """
    Sets a user's active status to FALSE, effectively disabling them.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET active = FALSE WHERE id = %s", (user_id,))
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Database error disabling user: {e}")
        conn.rollback()
        return False