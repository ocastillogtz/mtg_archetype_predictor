import json
import logging
import sys
import configparser
from app.classes.card_object import MagicCard

def read_json_file(file_path):
    with open(file_path, 'r', encoding="utf8") as file:
        data = file.read()
        if not data:
            raise ValueError("The file is empty.")
        dictionary = json.loads(data)
        return dictionary

def retrieve_source_json_data(file_path):
    try:
        card_dictionary = read_json_file(file_path)
    except ValueError as e:
        logging.error(f"The file {file_path} couldn't be opened because of the following error:\n" + str(e))
        return []
    card_data = []
    mcm_meta_ids_found_list = []
    for key1, value1 in card_dictionary["data"].items():
        for card_found in value1["cards"]:
            if "mcmMetaId" not in card_found["identifiers"]:
                continue
            try:
                current_mcm_meta_id = card_found.get("identifiers", {}).get("mcmMetaId", "")
                if not current_mcm_meta_id:
                    continue
                if current_mcm_meta_id not in mcm_meta_ids_found_list:
                    new_card = MagicCard.create(
                        id=current_mcm_meta_id,
                        name=card_found.get("name",""),
                        color=card_found.get("colors",[]),
                        converted_mana_cost=int(card_found.get("cost",0)),
                        mana_cost=card_found.get("manaCost",""),
                        card_type=card_found.get("types",[]),
                        power=card_found.get("power",0),
                        toughness=card_found.get("toughness", 0),
                        card_text=card_found.get("originalText",""),
                        subtypes=card_found.get("subtypes",[]),
                        mcm_meta_id=card_found.get("mcm_meta_id",""),
                        mtg_arena_id=card_found.get("identifiers", {}).get("mtgArenaId", ""),
                        super_types=card_found.get("supertypes", []),
                        tcg_player_link= card_found.get("links", {}).get("tcgplayer", ""),
                        card_market_link=card_found.get("links", {}).get("cardmarket", "")
                        )

                    if not new_card.card_text:
                        new_card.card_text=str(card_found.get("text",""))

                    if current_mcm_meta_id == "7761":
                        print(new_card)
                        print(card_found)
                    card_data.append(new_card)
                    mcm_meta_ids_found_list.append(current_mcm_meta_id)


            except Exception as e:
                logging.warning("An error happened while trying to parse the source data, we couldn't parse the following entry:\n" + str(
                        card_found) + "\n" + "Receives the following error message:\n" + str(e))

    number_of_cards_found = len(card_data)
    logging.debug(f"In the file {file_path} we found " + str(number_of_cards_found) + " cards.")

    return card_data

def test_parse_data_from_source():
    config = configparser.ConfigParser()
    config.read("C:\\Users\omar_\Documents\github\mtg_archetype_predictor\mtg_archetype_predictor\\test_config.ini")
    cards=retrieve_source_json_data(config["test_assets"]["parse_source_data"])
    for i in cards:
        print(i)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    test_parse_data_from_source()
