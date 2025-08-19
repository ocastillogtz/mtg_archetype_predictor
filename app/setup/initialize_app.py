import configparser
import logging
import os
import sys
from app.setup.vectorize_cards import vectorize_card_data
import pickle
from app.db.db_cards import insert_magic_cards_bulk
from app.db.db_initialization import initialize_db
from app.setup.parse_card_data import retrieve_source_json_data
import argparse
import logging
from pathlib import Path
from typing import Optional,Literal


STAGE_TO_FILENAME_MAPPING = {"dev":"config_dev.ini",
                             "DEV":"config_dev.ini",
                             "test":"config_test.ini",
                             "TEST":"config_test.ini",
                             "prod":"config_prod.ini",
                             "PROD":"config_prod.ini",
                             "production":"config_prod.ini"}

def get_config_path(filename: str = "config.ini") -> Optional[Path]:
    """
    Returns the Path to the config file located in the 'config' folder
    one level above the current script's directory.

    :param filename: Name of the config file (default: "config.ini")
    :return: Path object if the file exists, None otherwise
    """
    try:
        current_dir = Path(__file__).resolve().parent
        config_path = current_dir.parent / "config" / filename

        if not config_path.exists():
            logging.error(f"Config file not found: {config_path}")
            return None

        logging.info(f"Config file found: {config_path}")
        return config_path

    except Exception as ex:
        logging.error(f"Error while resolving config path: {ex}")
        return None



def initialize_mtg_archetype_predictor(config_file_path,hard_reset: bool) -> None:
    # Read Config file
    config = configparser.ConfigParser()
    config.read(config_file_path)

    # Check db
    if not initialize_db(config,hard_reset):
        raise Exception("Something went wrong while initializing the database.")
    # Load the DB with the card data, that contains some card metadata and the MagicCard classes and its vector data for
    # the machine learning model
    logging.debug("Parsing card data from source file")
    card_list = retrieve_source_json_data(config["source_data"]["json_data_filepath"])
    logging.debug("Vectorizing card data obtained")
    card_list = vectorize_card_data(card_list,config)
    logging.debug("Loading the whole card data in the db")
    insert_magic_cards_bulk(config,card_list)



def main():
    # --- CLI Argument Parsing ---
    parser = argparse.ArgumentParser(description="Run initialization.py script with stage and logging level.")

    # logging level argument with default
    parser.add_argument(
        "--log-level","-l",
        default="ERROR",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: ERROR)."
    )

    # logging level argument with default
    parser.add_argument(
        "--config","-c",
        help="Path to config file.",
        type = str,
        required = True,
    )

    parser.add_argument(
        '--hard-reset',  # the flag name
        action='store_true',  # True if present, False if absent
        help='Deletes all tables for ever, be careful'
    )

    args = parser.parse_args()

    # --- Logging Configuration ---
    logging.basicConfig(stream=sys.stdout, level=getattr(logging, args.log_level.upper()), format='%(asctime)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')
    if args.hard_reset:
        logging.warning(f"Be careful, you are doing a hard reset, you are deleting all your cards,users,everything")
    initialize_mtg_archetype_predictor(args.config,args.hard_reset)




if __name__ == "__main__":
    main()