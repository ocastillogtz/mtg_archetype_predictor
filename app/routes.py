from flask import request, session, redirect, g, render_template, url_for

from app.db.db_users import authenticate_user  # Function from db_users.py

def register_routes(app):

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error_message = ""
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            if authenticate_user(g.db_conn, username, password):
                session["authenticated"] = True
                return redirect("/home")
            error_message = "Invalid credentials"
        return render_template("login_page.html", error=error_message)

    @app.route('/')
    def root():
        # Redirect to home page
        return redirect(url_for('home'))

    @app.route("/home")
    def home():
        if not session.get("authenticated", False):
            return redirect("/login")
        username = session.get("username", "Unknown user")
        return f"<h1>Welcome {username} to the Home Page!</h1>"

    @app.route("/health")
    def health():
        return {"status": "ok"}

    @app.route("/logout")
    def logout():
        session.pop("authenticated", None)
        session.pop("username", None)
        return redirect("/login")
