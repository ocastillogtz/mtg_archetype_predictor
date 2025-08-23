import logging
import numpy as np
from app.db.db_cards import update_magic_card

def annotate_card(form_data,card_object):
    logging.info(f"Annotating the card: {card_object.name}")
    print(form_data)
    for i,j in form_data.items():
        print(i,j)

    for i in form_data:
        print(i)

    print("####################################")
    new_vec = []
    for label in card_object.vector_output_labels:
        print(label)
        for category, archetype in form_data.items():
            print("--" + archetype)
            if label == archetype:
                print("found")
                new_vec.append(1)
                break
        else:
            print("nofound")
            new_vec.append(0)

    print(new_vec)
    card_object.vector_output = np.array(new_vec,dtype=float)
    update_magic_card(card_object)
    return card_object
