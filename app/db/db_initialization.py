
import configparser
import logging
import psycopg2
from psycopg2 import sql
import json
import psycopg2.pool
from app.db.db_cards import create_cards_table
from app.db.db_users import create_users_table



def initialize_db(config,hard_reset):
    """

    :return:
    """
    connection = connect_to_db_no_user(config["postgresql"])
    if not check_if_database_exists(connection, config["postgresql"]["database"]):
        create_database(connection, config["postgresql"]["database"])
    create_user_to_manipulate_table(connection, config)
    connection.close()
    connection = connect_to_db_with_user(config)
    if hard_reset:
        drop_table(connection, "cards")
        drop_table(connection, "users")
    if not table_exists(connection, "cards"):
        create_cards_table(connection)
    check_table_entries_number(connection, "cards")
    if not table_exists(connection, "users"):
        create_users_table(connection)
    connection.close()
    return True


def create_user_to_manipulate_table(conn, config):
    """
    This creates the user that is going to manipulate the table in our application
    :param conn:
    :param config:
    :return:
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE ROLE {username} WITH
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            INHERIT
            NOREPLICATION
            NOBYPASSRLS
            CONNECTION LIMIT -1
            PASSWORD '{password}';""".format(username=config["database_user"]["user"],
                                             password=config["database_user"]["password"])
        )
        cur.execute(
            """GRANT ALL ON schema public TO {username};""".format(username=config["database_user"]["user"]))
        cur.execute("""ALTER DATABASE {database_name} OWNER TO {username};""".format(
            database_name=config["postgresql"]["database"], username=config["database_user"]["user"]))
        cur.close()
        return True

    except Exception as e:
        logging.warning(
            "Beware, something went bad while creating a user,we received the following message: \n" + str(e))
        cur.close()
        return False


def connect_to_db_no_user(config_postgres):
    """
    Connect to the PostgreSQL database server, but you do it with the initial credentials
    not as a user.

    :param config_postgres: this is the config object on the [postgresql] section (using the package configparser) that read our configuration
    file called: mtg_at_p.ini
    :return: connection object (using the package psycopg2) this allows us to interact with the database
    """

    try:
        with psycopg2.connect(user=config_postgres["user"],
                              password=config_postgres["password"],
                              host=config_postgres["host"],
                              port=config_postgres["port"]) as conn:
            logging.info('Connected to the PostgreSQL server.')
            conn.autocommit = True
            return conn
    except (psycopg2.DatabaseError, Exception) as error_message:
        logging.error(error_message)
        return error_message


def connect_to_db_with_user(config):
    """
    Connect to the PostgreSQL database server, but you do as a user, this user is going to be the one that manipulates
    the database and it is created during the database initialization process.

    :param config: this is the config object (using the package configparser) that read our configuration
    file called: mtg_at_p.ini
    :return: connection object (using the package psycopg2) this allows us to interact with the database
    """
    dbname = config["postgresql"]["database"]
    host = config["postgresql"]["host"]
    port = config["postgresql"]["port"]
    user = config["database_user"]["user"]
    password = config["database_user"]["password"]
    try:
        with psycopg2.connect(dbname=dbname,
                              user=user,
                              password=password,
                              host=host,
                              port=port) as conn:
            logging.info('Connected to the PostgreSQL server.')
            conn.autocommit = True
            return conn
    except (psycopg2.DatabaseError, Exception) as error_message:
        logging.error(error_message)
        return error_message



def get_conn():
    # Create a connection pool
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host="your_host",
        database="your_database",
        user="your_username",
        password="your_password"
    )

    # Get a connection from the pool
    conn = connection_pool.getconn()
    try:
        # Use the connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", ("test",))
        # ...
        conn.commit()
    finally:
        # Return the connection to the pool
        connection_pool.putconn(conn)


def table_exists(conn, table_name):
    """
    Checks if table exists, if exists return True, if not False

    :param conn: connection object from the package psycopg2
    :param table_name: the name of the table
    :return:
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM 
                pg_tables
            WHERE 
                schemaname = 'public' AND 
                tablename  = '{table_name}'
        );
    """.format(table_name=table_name))
    try:
        findings = cur.fetchone()[0]
        # Close the cursor
        cur.close()
        if str(findings) == "False":
            logging.info(f"the table {table_name} wasn't found.")
            return False
        else:
            logging.info(f"the table {table_name} already exists. Found this: " + str(findings))
            return True
    except TypeError as e:
        logging.error(
            f"Tried to create a table with the name {table_name}, but FAILED, received the following message.\n" + str(
                e))
        # Close the cursor
        cur.close()
        return False


def check_table_entries_number(conn, table_name):
    """
    obtain the number of entries in the table with the table name given

    :param conn:
    :param table_name:
    :return: entry_count
    """
    cur = conn.cursor()
    cur.execute("""
          SELECT count(*) FROM {table_name};
      """.format(table_name=table_name))
    try:
        findings = cur.fetchone()[0]
        logging.info("found the following number of entries: " + str(findings))
        # Close the cursor
        cur.close()
        return findings
    except TypeError as e:
        logging.error(
            f"Tried to check if a table with the name {table_name} exists, but FAILED, received the following message.\n" + str(
                e))
        # Close the cursor
        cur.close()
        return False



def check_if_database_exists(conn, database_name):
    """
    Checks if database exists given a database name

    :param conn:
    :param database_name:
    :return: True if exists, False if not
    """
    # Create a cursor object
    cur = conn.cursor()
    # Check if the database already exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname='{database_name}';".format(database_name=database_name))
    try:
        if cur.fetchone():
            logging.info(f"Database '{database_name}' already exists.")
            return True
        else:
            logging.info(f"Database '{database_name}' doesn't exist.")
            return False
    except Exception as e:
        logging.info(
            f"Somethign went wrong creating the database '{database_name}' received the following message: " + str(e))
        return False


def create_database(conn, database_name):
    """
    Creates a database given a database name
    :param conn:
    :param database_name:
    :return:
    """
    # Create a cursor object
    cur = conn.cursor()
    # Create the table
    cur.execute("""CREATE DATABASE {database_name};""".format(database_name=database_name))
    logging.info(f"The database {database_name} has been created")
    # Close the cursor and the connection
    cur.close()
    return True


def drop_table(conn, table_name):
    """
    Drops the specified table safely.

    Args:
        conn: psycopg2 connection object.
        table_name (str): Name of the table to drop.
    """
    try:
        with conn.cursor() as cur:
            # Check if table exists before dropping
            check_query = sql.SQL("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                );
            """)
            cur.execute(check_query, (table_name,))
            exists = cur.fetchone()[0]

            if exists:
                drop_query = sql.SQL("DROP TABLE {} CASCADE;").format(sql.Identifier(table_name))
                cur.execute(drop_query)
                logging.info(f"Table '{table_name}' dropped successfully.")
            else:
                logging.warning(f"Table '{table_name}' does not exist. Skipping drop.")

        conn.commit()

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        logging.error(f"Failed to drop table '{table_name}': {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    config = configparser.ConfigParser()
    config.read("mtg_at_p_test.ini")
    conn = connect_to_db_with_user(config)
