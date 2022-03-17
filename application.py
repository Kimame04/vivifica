from flask import Flask, render_template, redirect, request, session
from flask_session import Session

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/feedback")
def feedback():
    return render_template("feedback.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        session["username"] = request.form.get("username")
        return redirect("/records")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session["username"] = None
    return redirect("/records")

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

@app.route("/records")
def records():
    if not session.get("username"): 
        return redirect("/login")
    return render_template("records.html")

@app.route("/bye")
def bye():
    return render_template("bye.html")


if __name__ == "__main__":
    app.run(debug=True)