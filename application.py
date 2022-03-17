from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("/index.html", data='user')

@app.route("/index.html")
def home():
    return render_template("/index.html", data='user')

@app.route("/feedback.html")
def feedback():
    return render_template("/feedback.html")

@app.route("/login.html")
def login():
    return render_template("/login.html")

@app.route("/pricing.html")
def pricing():
    return render_template("/pricing.html")

@app.route("/records.html")
def records():
    return render_template("/records.html")

@app.route("/bye")
def bye():
    return render_template("bye.html")
    
@app.route('/<name>')
def custom(name):
    return render_template("index.html", data = name)

if __name__ == "__main__":
    app.run(debug=True)