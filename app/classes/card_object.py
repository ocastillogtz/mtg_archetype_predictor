
MANA_COST_MAPPING = {
    "W":"&#127774;",
    "B":"&#128128;",
    "R":"&#128293;",
    "G":"&#127795;",
    # U means Blue
    "U":"&#128167;",
    "C":"&#128280;",
    "1":"&#x0031;",
    "2":"&#x0032;",
    "3":"&#51;",
    "4":"&#52;",
    "5":"&#53;",
    "6":"&#54;",
    "7":"&#55;",
    "8":"&#56;",
    "9":"&#57;",
    "X":"&#42;",
    "unknown": "&#10068;"

}

CARD_COLOR_MAPPING = {
    "W": "beige",
    "B": "Lavender",
    "R": "crimson",
    "G": "forestgreen",
    # U means Blue
    "U": "royalblue",
    "colorless": "AliceBlue",
    "multicolor": "goldenrod",
    "unknown": "&#10068;"
}

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import re
import numpy as np

@dataclass
class MagicCard:
    id: int
    converted_mana_cost: int
    mtg_arena_id: int
    name: str
    color: List[str]
    mana_cost: str
    card_type: List[str]
    subtypes: List[str]
    super_types: List[str]
    card_text: str
    power: int
    toughness: int
    mcm_meta_id: int
    card_market_link: str
    tcg_player_link: str
    vector_input: Optional[np.ndarray] = field(default=None, init=False, repr=False, compare=False)
    vector_output: Optional[np.ndarray] = field(default=None, init=False, repr=False, compare=False)
    vector_input_labels: List[str] = field(default_factory=list, init=False, repr=False, compare=False)
    vector_output_labels: List[str] = field(default_factory=list, init=False, repr=False, compare=False)
    predicted_archetypes: List[str] = field(default_factory=list)
    annotated_archetypes: List[str] = field(default_factory=list)
    gold_standard_archetypes: List[str] = field(default_factory=list)

    # This will be computed dynamically
    display_mana_cost: str = ""
    display_color: str = ""
    display_card_type: str = ""
    display_card_subtype: str = ""
    display_html: str = "<div><p>Render not available</p></div>"

    @classmethod
    def create(cls, **kwargs) -> "MagicCard":
        kwargs["display_color"] = get_display_color(kwargs.get("color", []))
        kwargs["display_mana_cost"] = get_display_mana_cost(kwargs.get("mana_cost", ""))
        kwargs["display_card_type"] = get_display_card_type_or_subtype(kwargs.get("card_type", []))
        kwargs["display_card_subtype"] = get_display_card_type_or_subtype(kwargs.get("subtypes", []))
        # Path to the folder containing your templates
        template_dir = Path(__file__).resolve().parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("card_template.html")
        card = cls(**kwargs)
        card.display_html = template.render(card=card)
        return card

    def update_vectors(self, input_vector_dict: Dict[str, float],
                       output_vector_dict: Optional[Dict[str, float]] = None):
        """
        Update MagicCard object with input/output vectors and their labels.

        :param input_vector_dict: dict {label: value} for input features
        :param output_vector_dict: dict {label: value} for output targets (optional)
        """
        # Store labels and values for input vector
        self.vector_input_labels = list(input_vector_dict.keys())
        self.vector_input = np.array(list(input_vector_dict.values()), dtype=float)

        # If output vector is provided
        if output_vector_dict is not None:
            self.vector_output_labels = list(output_vector_dict.keys())
            self.vector_output = np.array(list(output_vector_dict.values()), dtype=float)

def get_display_color(entry):
    if len(entry) > 1:
        return CARD_COLOR_MAPPING["multicolor"]
    elif len(entry) == 1:
        return CARD_COLOR_MAPPING.get(entry[0], CARD_COLOR_MAPPING["unknown"])
    else:
        return CARD_COLOR_MAPPING["colorless"]

def get_display_card_type_or_subtype(entry):
    if entry:
        return " ".join(entry)
    else:
        return ""
def get_display_mana_cost(entry):
    if not entry:
        return ""
    else:
        display_mana_cost = ""
        for character in entry:
            display_mana_cost = display_mana_cost + MANA_COST_MAPPING[character]

        return display_mana_cost

"""
Card example


    Card Example:
        {
          "color": ["W"],
          "cost": 7.0,
          "cardtype": ["Creature"],
          "supertypes": [],
          "subtypes": ["Human", "Cleric"],
          "name": "Ancestor's Chosen",
          "links": {
            "cardKingdom": "https://mtgjson.com/links/9fb51af0ad6f0736",
            "cardmarket": "https://mtgjson.com/links/ace8861194ee0b6a",
            "tcgplayer": "https://mtgjson.com/links/4843cea124a0d515"
          },
          "mcm_meta_id": "156",
          "sources": {
            "cardKingdomId": "122719",
            "cardsphereFoilId": "19",
            "cardsphereId": "20",
            "mcmId": "16165",
            "mcmMetaId": "156",
            "mtgjsonFoilVersionId": "b7c19924-b4bf-56fc-aa73-f586e940bd42",
            "mtgjsonV4Id": "ad41be73-582f-58ed-abd4-a88c1f616ac3",
            "mtgoFoilId": "27501",
            "mtgoId": "27500",
            "multiverseId": "130550",
            "scryfallCardBackId": "0aeebaf5-8c7d-4636-9e82-8c27447861f7",
            "scryfallId": "7a5cd03c-4227-4551-aa4b-7d119f0468b5",
            "scryfallIllustrationId": "be2f7173-c8b7-4172-a388-9b2c6b3c16e5",
            "scryfallOracleId": "fc2ccab7-cab1-4463-b73d-898070136d74",
            "tcgplayerProductId": "15032"
          },
          "power": "4",
          "toughness": "4",
          "originalText": "First strike\nWhen Ancestor's Chosen comes into play, you gain 1 life for each card in your graveyard."
        }

"""