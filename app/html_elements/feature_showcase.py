from flask import render_template

def get_feature_showcase():
    feature_cards = [{
        "image": "dash.jpg",
        "title":"Dashboard",
        "link":"/dashboard",
        "description":"Get insight on the data charactersitics in the dashboard"
    },{
        "image": "annotate.jpg",
        "title": "Annotate a random card",
        "link": "/annotate_random_card",
        "description": "Get a random card to be annotated."
    }]
    return render_template("showcase_features_template.html",cards=feature_cards)