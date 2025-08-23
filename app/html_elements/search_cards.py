
from app.db.db_utils import execute_query
import logging
from flask import render_template


def search_cards(request):
    try:
        name = request.args.get("name", "").strip()
        colors = request.args.getlist("colors")  # multiple checkboxes
        card_type = request.args.get("card_type", "").strip()
        if card_type:
            card_type = [request.args.get("card_type", "").strip()]
        else:
            card_type = []
        cmc = request.args.get("converted_mana_cost", "").strip()
        card_text = request.args.get("card_text", "").strip()

        # Base query
        query = """
        SELECT id, mtg_arena_id, name, color, mana_cost, card_type, subtypes, super_types,
               card_text, power, toughness, mcm_meta_id, card_market_link, tcg_player_link,
               predicted_archetypes, annotated_archetypes, gold_standard_archetypes
        FROM cards
        WHERE 1=1
        """

        params = []

        # Add conditions dynamically
        if name:
            query += " AND name ILIKE %s"
            params.append(f"%{name}%")

        if card_text:
            query += " AND card_text ILIKE %s"
            params.append(f"%{card_text}%")

        if colors:
            # Match any color in the array
            query += " AND ("
            query += " OR ".join(["%s = ANY(color)" for _ in colors])
            query += ")"
            params.extend(colors)

        if card_type:
            # Match any color in the array
            query += " AND ("
            # here we have to fake that the source is coming from a list of card_types, it is not, but I don't want to make a very advance search, only something easy.
            query += " OR ".join(["%s = ANY(card_type)" for _ in card_type])
            query += ")"
            params.extend(card_type)

        if cmc:
            query += " AND converted_mana_cost = %s"
            params.append(cmc)

        print(query)

        # Execute
        rows = execute_query(query, params, fetch=True)

        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "mtg_arena_id": row[1],
                "name": row[2],
                "color": row[3],
                "mana_cost": row[4],
                "card_type": row[5],
                "subtypes": row[6],
                "super_types": row[7],
                "card_text": row[8],
                "power": row[9],
                "toughness": row[10],
                "mcm_meta_id": row[11],
                "card_market_link": row[12],
                "tcg_player_link": row[13],
                "predicted_archetypes": row[14],
                "annotated_archetypes": row[15],
                "gold_standard_archetypes": row[16]
            })

        data_consult_form = render_template("card_data_consultation_form.html")
        color_emojis = {'W': '☀️', 'U': '💧', 'B': '💀', 'R': '🔥', 'G': '🌳'}
        return render_template("search_results.html", data_consultation_form=data_consult_form, results=result,
                               color_emojis=color_emojis)

    except Exception as e:
        logging.error(f"Advanced search failed: {e}")
        return "<div><p>Query Failed</p></div>"


