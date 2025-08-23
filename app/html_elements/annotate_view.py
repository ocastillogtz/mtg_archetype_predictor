import configparser
from flask import render_template

def get_annotate_view(card_object):
    archetype_label_checkbox_status_pair_dict = {}
    for arch_checkbox_status, archetype_labels in zip(card_object.vector_output,card_object.vector_output_labels):
        if arch_checkbox_status < 0.1:
            archetype_label_checkbox_status_pair_dict[archetype_labels] = ""
        else:
            archetype_label_checkbox_status_pair_dict[archetype_labels] = "checked"
    return render_template("annotate_view.html", card_display=card_object.display_html,archetype_data=archetype_label_checkbox_status_pair_dict)
