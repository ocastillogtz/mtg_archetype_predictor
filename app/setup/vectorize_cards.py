import logging
import os
import sys
import configparser
from app.setup.parse_card_data import retrieve_source_json_data
import pickle
import pandas as pd
import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Set

from concurrent.futures import ProcessPoolExecutor, wait, as_completed,ALL_COMPLETED

CHARACTERS_TO_BE_REPLACED = ["\n",".",",",":","(",")","\"","•","—"]
NUMBER_OF_CPU_CORES = 12

def vectorize_card_data(cards,config):
    color_set_all_cards = set()
    card_type_all_cards = set()
    super_type_all_cards = set()
    sub_type_all_cards = set()

    if not "host_parameters" in config:
        logging.warning("There are no host_parameters in the config file, therefore we are using 1 as the number of CPUs.")
        NUMBER_OF_CPU_CORES = 1
    else:
        if not "number_of_cpu_cores" in config["host_parameters"]:
            logging.warning("There are no number_of_cpu_cores in \"host_parameters\" in the config file, therefore we are using 1 as the number of CPUs.")
            NUMBER_OF_CPU_CORES = 1
        else:
            if not represents_int(config["host_parameters"]["number_of_cpu_cores"]):
                logging.warning("The number of CPUs given seems to be not an integer, received this value: " + str(config["host_parameters"]["number_of_cpu_cores"]) + "\nWe are using a 1 as the number of CPUs")
                NUMBER_OF_CPU_CORES = 1

            else:
                logging.debug("Using the following number of CPU cores to process the data: " + str(config["host_parameters"]["number_of_cpu_cores"]))
                NUMBER_OF_CPU_CORES = int(config["host_parameters"]["number_of_cpu_cores"])


    # Create a ProcessPoolExecutor with 4 worker processes
    logging.debug("Starting card data parsing")
    with ProcessPoolExecutor(max_workers=NUMBER_OF_CPU_CORES) as executor:
        # Use the executor to map the function to the input data
        card_categories_sets = executor.map(get_sets_of_data_in_card, cards)
    logging.debug("Ended card data parsing")
    for single_card_categories_sets in card_categories_sets:
        color_set_all_cards.update(single_card_categories_sets["color"])
        super_type_all_cards.update(single_card_categories_sets["supertypes"])
        sub_type_all_cards.update(single_card_categories_sets["subtypes"])
        card_type_all_cards.update(single_card_categories_sets["card_type"])
    total_colors = len(color_set_all_cards)
    logging.info("In this data there are {number} different types of colors".format(number=str(total_colors)))
    total_cardtypes = len(card_type_all_cards)
    logging.info("In this data there are {number} different types of cardtypes".format(number=str(total_cardtypes)))
    total_supertypes = len(super_type_all_cards)
    logging.info("In this data there are {number} different types of supertypes".format(number=str(total_supertypes)))
    total_subtypes = len(sub_type_all_cards)
    logging.info("In this data there are {number} different types of subtypes".format(number=str(total_subtypes)))


    g_labels_for_items_not_in_the_model = {"meta_name": "name",
                                           "meta_links": "links",
                                           "meta_mcm_meta_id": "mcm_meta_id",
                                           "meta_sources": "sources"}

    g_non_categorical_values_labels = {"input_cost": "cost",
                                       "input_power": "power",
                                       "input_toughness": "toughness"}

    g_color_labels = {"input_color_" + str(color) : color for color in color_set_all_cards}
    logging.debug("We found the following color labels: " + str(g_color_labels))

    g_cardtypes_labels = {"input_cardtypes_" + str(cardtype) : cardtype for cardtype in card_type_all_cards}
    logging.debug("We found the following cardtype labels: " + str(g_cardtypes_labels))

    g_supertypes_labels = {"input_supertypes_" + str(supertype) : supertype for supertype in super_type_all_cards}
    logging.debug("We found the following supertype labels: " + str(g_supertypes_labels))

    g_subtypes_labels = {"input_subtypes_" + str(subtype) : subtype for subtype in sub_type_all_cards}
    logging.debug("We found the following subtype labels: " + str(g_subtypes_labels))

    relevant_words_in_card_text = count_repeated_words([card.card_text for card in cards])
    g_word_labels = {"input_word_" + str(word) : word for word in relevant_words_in_card_text}
    logging.debug("We found the following relevant words labels: " + str(g_subtypes_labels))

    logging.debug("Starting card data vectorizing")
    card_vector_list = []
    with ProcessPoolExecutor(max_workers=NUMBER_OF_CPU_CORES) as executor:
        # Use the executor to map the function to the input data
        # submit tasks and collect futures
        futures = [executor.submit(get_card_vector, card,local_id,g_non_categorical_values_labels,g_color_labels,g_cardtypes_labels,g_supertypes_labels,g_subtypes_labels,g_word_labels) for local_id,card in enumerate(cards)]

    done_futures, not_done_futures = wait(futures, return_when=ALL_COMPLETED)
    input_card_vector_list = [future.result() for future in done_futures]

    g_archetype_labels = {"output_archetype_" + str(x) : str(x) for x in list(config["fixed_data"]["archetypes"].split(","))}
    logging.debug("We found the following archetype labels: " + str(g_subtypes_labels))

    output_vector = {}
    for label_output in g_archetype_labels:
        output_vector[label_output] = 0


    logging.info("Number of cards successfully vectorized: " + str(len(card_vector_list)))
    logging.debug("Ended card data vectorizing")


    card_vectors_data = sorted(card_vector_list, key=lambda x: int(x["local_id"]))

    for card,vector in zip(cards,input_card_vector_list):
        card.update_vectors(vector,output_vector)

    return cards


def get_card_vector(card,local_id,g_non_categorical_values_labels,g_color_labels,g_cardtypes_labels,g_supertypes_labels,g_subtypes_labels,g_word_labels):
    """
    Convert card data into card data + card vector

    :param card:
    :param local_id:
    :param g_labels_for_items_not_in_the_model:
            {
               "meta_name": "name",
               "meta_links": "links",
               "meta_mcm_meta_id": "mcm_meta_id",
               "meta_sources": "sources"
           }
    :param g_non_categorical_values_labels:
            {
               "input_cost": "cost",
               "input_power": "power",
               "input_toughness": "toughness"
           }
    :param g_color_labels: Dictionary of card data that we want in out reduce data and it is categorical
        {"":""}

    :param g_cardtypes_labels:
    :param g_supertypes_labels:
    :param g_subtypes_labels:
    :param g_word_labels:
    :param g_archetype_labels:
    :return:
    """

    entry = {}
    entry["local_id"] = local_id


    for non_categorical_data_label_output, non_categorical_data_label_indata in g_non_categorical_values_labels.items():
        value = getattr(card, non_categorical_data_label_indata, "")
        if value and represents_int(value):
            entry[non_categorical_data_label_output] = int(value)
        else:
            entry[non_categorical_data_label_output] = 0

    for label_output, label_in_data in g_color_labels.items():
        colors = getattr(card, "color", "")
        entry[label_output] = 1 if label_in_data in colors else 0

    for label_output, label_in_data in g_cardtypes_labels.items():
        cardtypes = getattr(card, "card_type", "")
        entry[label_output] = 1 if label_in_data in cardtypes else 0

    for label_output, label_in_data in g_supertypes_labels.items():
        supertypes = getattr(card, "supertypes", "")
        entry[label_output] = 1 if label_in_data in supertypes else 0

    for label_output, label_in_data in g_subtypes_labels.items():
        subtypes = getattr(card, "subtypes", "")
        entry[label_output] = 1 if label_in_data in subtypes else 0

    for label_output, label_in_data in g_word_labels.items():
        current_text_words = getattr(card, "originalText", "")
        entry[label_output] = 1 if label_in_data in current_text_words else 0

    return entry

def get_sets_of_data_in_card(card):
    card_type_set = set(card.card_type)
    super_type_set = set(card.super_types)
    sub_type_set = set(card.subtypes)
    color_set = set(card.color)
    card_categories_set = {
        "color" : color_set,
        "supertypes": super_type_set,
        "subtypes": sub_type_set,
        "card_type": card_type_set
    }
    return card_categories_set

def represents_int(s):
    try:
        int(s)
    except ValueError:
        return False
    else:
        return True


def tokenize_text(text: str) -> List[str]:
    """
    Split a string into words, considering spaces, newlines, punctuation, etc.
    Converts to lowercase.
    """
    return re.findall(r'\b\w+\b', text.lower())


def count_words_in_chunk(texts: List[str]) -> Counter:
    """
    Count words in a chunk of texts.
    """
    counter = Counter()
    for text in texts:
        words = tokenize_text(text)
        counter.update(words)
    return counter


def count_repeated_words(texts: List[str], max_workers: int = 4) -> Set[str]:
    """
    Count words in a list of strings and return only those that appear more than once.

    :param texts: List of input strings
    :param max_workers: Number of processes for parallelization
    :return: Set of repeated words
    """
    if not texts:
        return set()

    # Split texts into chunks for parallel processing
    chunk_size = max(1, len(texts) // max_workers)
    chunks = [texts[i:i + chunk_size] for i in range(0, len(texts), chunk_size)]

    total_counter = Counter()

    # Parallel processing
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(count_words_in_chunk, chunk) for chunk in chunks]
        for future in as_completed(futures):
            total_counter.update(future.result())

    # Keep only words that appear more than once
    repeated_words = {word for word, count in total_counter.items() if count > 1}
    return repeated_words


def test_vectorize_card_data():
    config = configparser.ConfigParser()
    config.read("C:\\Users\omar_\Documents\github\mtg_archetype_predictor\mtg_archetype_predictor\\test_config.ini")
    cards=retrieve_source_json_data(config["test_assets"]["parse_source_data"])
    vectorize_card_data(cards,config)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    test_vectorize_card_data()




