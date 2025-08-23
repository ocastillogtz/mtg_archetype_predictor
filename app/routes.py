from flask import request, session, redirect, g, render_template, url_for
from app.html_elements.navbar import get_navbar
from app.html_elements.feature_showcase import get_feature_showcase
from app.html_elements.search_cards import search_cards
from app.html_elements.annotate_view import get_annotate_view
from app.functions.update_archetypes import annotate_card
from app.db.db_users import authenticate_user
from app.db.db_cards import get_magic_card
from flask import request
import configparser

def register_routes(app,config):

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error_message = ""
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            if authenticate_user(g.db_conn, username, password):
                session["authenticated"] = True
                session["username"] = username
                session["active_page"] = "home"
                return redirect("/home")
            error_message = "Invalid credentials"
        return render_template("login_page.html", error=error_message)

    @app.route('/')
    def root():
        if not session.get("authenticated", False):
            return redirect("/login")
        # Redirect to home page
        return redirect(url_for('home'))

    @app.route('/cards', methods=['GET'])
    def search_cards_route():
        if not session.get("authenticated", False):
            return redirect("/login")
        if request.method == "GET":
            if any(value for value in request.args.values()):
                page_content = search_cards(request)
                return get_navbar(session,page_content)
            else:
                data_consult_form = render_template("card_data_consultation_form.html")
                return get_navbar(session, data_consult_form)

    @app.route('/annotate', methods=['GET'])
    def get_random_card():
        if not session.get("authenticated", False):
            return redirect("/login")
        return redirect("/annotate/423")


    @app.route('/annotate/<int:card_id>', methods=['POST', 'GET'])
    def submit_card_annotation(card_id):
        if not session.get("authenticated", False):
            return redirect("/login")

        if request.method == 'POST' or request.method == "post":
            card_object = annotate_card(request.form,get_magic_card(card_id))
            return get_navbar(session, get_annotate_view(card_object))

        elif request.method == 'GET':
            card_object = get_magic_card(card_id)
            if card_object:
                return get_navbar(session, get_annotate_view(card_object))
            else:
                return get_navbar(session, "<div><p>Card not found</p></div>")
        else:
            return redirect("/login")



    @app.route("/home")
    def home():
        if not session.get("authenticated", False):
            return redirect("/login")
        page_content = get_feature_showcase()
        return get_navbar(session,page_content)

    @app.route("/health")
    def health():
        return {"status": "ok"}

    @app.route("/logout")
    def logout():
        session.pop("authenticated", None)
        session.pop("username", None)
        return redirect("/login")
