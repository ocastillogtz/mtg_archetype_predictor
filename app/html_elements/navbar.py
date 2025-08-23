from flask import render_template

def get_navbar(session,sub_page_content):
    return render_template("navbar_and_blank_page.html",session=session,sub_page_content=sub_page_content)