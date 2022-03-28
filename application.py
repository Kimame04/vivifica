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
app.config['MYSQL_DB'] = 'vivifica'

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
        cursor.execute('SELECT * FROM account WHERE username = %s', (username,))
        account = cursor.fetchone()

        if request.form["submit_btn"] == "login": 
            if account and password == account["password"]:
                session['loggedin'] = True
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
                cursor.execute('INSERT INTO account VALUES (%s, %s, %s)', (username, password, email,))
                mysql.connection.commit()
                cursor.execute('SELECT * FROM account WHERE username = %s', (username,))
                account = cursor.fetchone()
                session['loggedin'] = True
                session['username'] = account['username']
                return redirect("/register")
    return render_template("login.html")

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == 'POST' and 'email' in request.form:
        email = request.form.get('email')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE account set email = %s where username = %s', (email, session["username"]))
        mysql.connection.commit()
        return redirect('/')
    return render_template("register.html")

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

@app.route("/parts", methods = ["GET", "POST"])
def parts():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and 'query' in request.form:
        query = request.form.get('query')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        list = ''
        val = request.form.get('sort')
        if val == '1':
            list = 'ORDER BY p_name ASC'
        if val == '2':
            list = 'ORDER BY p_name DESC'
        if val == '3':
            list = 'ORDER BY c_name ASC'
        if val == '4':
            list = 'ORDER BY c_name DESC'

        cursor.execute('SELECT * FROM part WHERE p_name LIKE %s  or c_name LIKE %s' + list, ['%%' + query + '%%', '%%' + query + '%%'])
        
        table = None
        if request.form.getlist('check'):
            table = 'true'
        
        return render_template("parts.html", parts=cursor.fetchall(), search="true", table=table)

    cursor.execute('SELECT * FROM part')
    return render_template("parts.html", parts=cursor.fetchall())

@app.route("/aircraft", methods = ["GET", "POST"])
def aircraft():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and 'query' in request.form:
        query = request.form.get('query')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        val = request.form.get('sort')
        if val == '1':
            list = 'ORDER BY reg_num ASC'
        if val == '2':
            list = 'ORDER BY reg_num DESC'
        if val == '3':
            list = 'ORDER BY aircraft_name ASC'
        if val == '4':
            list = 'ORDER BY aircraft_name DESC'

        cursor.execute('SELECT * FROM produced_as WHERE aircraft_name LIKE %s  or reg_num LIKE %s' + list, ['%%' + query + '%%', '%%' + query + '%%'])
        table = None
        if request.form.getlist('check'):
            table = 'true'

        return render_template("aircraft.html", aircrafts=cursor.fetchall(), search="true", table=table)

    cursor.execute('SELECT * FROM produced_as')
    return render_template("aircraft.html", aircrafts=cursor.fetchall())

@app.route("/maintenance", methods = ["GET", "POST"])
def maintenance():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and 'query' in request.form:
        query = request.form.get('query')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        val = request.form.get('sort')
        if val == '1':
            list = 'ORDER BY reg_num ASC'
        if val == '2':
            list = 'ORDER BY reg_num DESC'
        if val == '3':
            list = 'ORDER BY date ASC'
        if val == '4':
            list = 'ORDER BY date DESC'
        
        cursor.execute('SELECT * FROM maintenance WHERE c_name LIKE %s  or facility_loc LIKE %s' + list, ['%%' + query + '%%', '%%' + query + '%%'])
        table = None
        if request.form.getlist('check'):
            table = 'true'
        return render_template("maintenance.html", records=cursor.fetchall(), search="true", table=table)

    cursor.execute('SELECT * FROM maintenance')
    return render_template("maintenance.html", records=cursor.fetchall())

@app.route("/company", methods = ["GET", "POST"])
def company():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and 'query' in request.form:
        query = request.form.get('query')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        val = request.form.get('sort')
        if val == '1':
            list = 'ORDER BY c_name ASC'
        if val == '2':
            list = 'ORDER BY c_name DESC'
        if val == '3':
            list = 'ORDER BY est_date ASC'
        if val == '4':
            list = 'ORDER BY est_date DESC'

        cursor.execute('SELECT * FROM company WHERE c_name LIKE %s' + list, ['%%' + query + '%%'])
        table = None
        if request.form.getlist('check'):
            table = 'true'
        return render_template("company.html", companies=cursor.fetchall(), search="true", table=table)
            
    cursor.execute('SELECT * FROM company')
    return render_template("company.html", companies=cursor.fetchall())


if __name__ == "__main__":
    app.run(debug=True)