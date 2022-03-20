from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'pythonlogin'

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/feedback")
def feedback():
    return render_template("feedback.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form.get("username")
        password = request.form.get("password")
        email = 'todo@todo.com'

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()

        if request.form["submit_btn"] == "login": 
            if account and password == account["password"]:
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                return redirect("/records")
            else:
                return render_template('login.html', message = "Invalid username or password!")

        else: 
            if account:
                return render_template('login.html', message = "Account already exists!")
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                return render_template('login.html', message = "Invalid email address!")
            elif not re.match(r'[A-Za-z0-9]+', username):
                return render_template('login.html', message = "Username must only contain characters or numbers!")
            elif not username or not password or not email:
                return render_template('login.html', message = "Form incomplete!")
            else:
                cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
                mysql.connection.commit()
                cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
                account = cursor.fetchone()
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                return redirect("/records")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session["username"] = None
    session["loggedin"] = None
    session["id"] = None
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