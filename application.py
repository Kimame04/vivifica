from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import sys
from datetime import datetime
import random
import string

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'vivifica'

mysql = MySQL(app)

C_NAME = None
EST_DATE = None
ADDRESS = None
FUNCTIONS = None

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

@app.route("/records", methods=["GET","POST"])
def records():
    if not session.get("username"): 
        return redirect("/login")
    if request.method == 'POST' and "contribute" in request.form:
        return redirect('/contribute')
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

        cursor.execute('SELECT * FROM aircraft WHERE aircraft_name LIKE %s  or reg_num LIKE %s' + list, ['%%' + query + '%%', '%%' + query + '%%'])
        table = None
        if request.form.getlist('check'):
            table = 'true'

        return render_template("aircraft.html", aircrafts=cursor.fetchall(), search="true", table=table)

    cursor.execute('SELECT * FROM aircraft')
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

@app.route("/type", methods = ["GET", "POST"])
def type():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and 'query' in request.form:
        query = request.form.get('query')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        val = request.form.get('sort')
        if val == '1':
            list = 'ORDER BY aircraft_name ASC'
        elif val == '2':
            list = 'ORDER BY aircraft_name DESC'
        elif val == '3':
            list = 'ORDER BY c_name ASC'
        elif val == '4':
            list = 'ORDER BY c_name DESC'

        cursor.execute('SELECT * FROM aircraft_type WHERE c_name LIKE %s' + list, ['%%' + query + '%%'])
        table = None
        if request.form.getlist('check'):
            table = 'true'
        return render_template("type.html", types=cursor.fetchall(), search="true", table=table)
            
    cursor.execute('SELECT * FROM aircraft_type')
    return render_template("type.html", types=cursor.fetchall())

@app.route('/contribute', methods=['GET', 'POST'])
def contribute():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if not session.get("username"): 
        return redirect("/login")
    if request.method == 'POST' and "part_1" in request.form:
        val = request.form.get('next')
        data = None
        data2 = None
        if val == '1' or val == '3':
            cursor.execute('SELECT c_name FROM company')
            data = cursor.fetchall()
        elif val == '2':
            cursor.execute('SELECT aircraft_name FROM aircraft_type')
            data = cursor.fetchall()
        elif val == '4':
            cursor.execute('SELECT c_name FROM company')
            data = cursor.fetchall()
            cursor.execute('SELECT reg_num from aircraft')
            data2 = cursor.fetchall()
        return render_template('contribute.html', val=val, data=data, data2=data2)
    if request.method == 'POST' and "type_submit" in request.form:
        name = request.form.get('name').replace(' ','')
        company = request.form.get('manu')
        year = request.form.get('year').replace(' ', '')
        engines = request.form.get('engines').replace(' ', '')
        size = request.form.get('size')
        cursor.execute('INSERT into aircraft_type VALUES (%s, %s, %s, %s, %s)', (name, company, year, size, engines,))
        mysql.connection.commit()
        return redirect('/records')
    elif request.method == 'POST' and "aircraft_submit" in request.form:
        name = request.form.get('name').replace(' ','')
        model = request.form.get('model')
        date = datetime.strptime(request.form.get('date'),'%Y-%m-%d')
        site = request.form.get('site').replace(' ', '')
        cursor.execute("INSERT into aircraft VALUES (%s, %s, %s, %s)", (name, model, date, site,))
        mysql.connection.commit()
        return redirect('/records')
    elif request.method == 'POST' and 'part_submit' in request.form:
        p_name = request.form.get('p_name').replace(' ', '')
        c_name = request.form.get('company')
        cost = request.form.get('cost')
        p_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 20))
        cursor.execute("INSERT into part VALUES (%s, %s, %s, %s)", (p_id, p_name, c_name, cost,))
        mysql.connection.commit()
        return redirect('/records')
    elif request.method == 'POST' and 'maintenance_submit' in request.form:
        m_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 20))
        c_name = request.form.get('company')
        date = datetime.strptime(request.form.get('date'),'%Y-%m-%d')
        facility_loc = request.form.get('facility_loc').replace(' ', '')
        summary = request.form.get('summary').replace(' ', '')
        reg_num = request.form.get('reg_num')
        cursor.execute("INSERT into maintenance VALUES (%s, %s, %s, %s, %s, %s)", (m_id, c_name, date, facility_loc, summary, reg_num,))
        mysql.connection.commit()
        return redirect('/records')
    elif request.method == 'POST' and 'company_next' in request.form:
        C_NAME = request.form.get('c_name')
        EST_DATE = request.form.get('est_date')
        ADDRESS = request.form.get('address')
        isProvider = int(str(request.form.get('provider')).replace('None', '0').replace('on', '1'))
        isManufacturer = int(str(request.form.get('manufacturer')).replace('None', '0').replace('on', '1'))
        isSupplier = int(str(request.form.get('supplier')).replace('None', '0').replace('on', '1'))
        isAirline = int(str(request.form.get('airline')).replace('None', '0').replace('on', '1'))
        FUNCTIONS = [isProvider, isManufacturer, isSupplier, isAirline]
        if isManufacturer == '1' or isAirline == '1':
            return render_template('contribute.html', val='6', data=FUNCTIONS)
        else: 
            cursor.execute("INSERT into company VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (C_NAME, EST_DATE, ADDRESS, isProvider, isManufacturer, None, isAirline, None, None, isSupplier,))
            mysql.connection.commit()
            return redirect('/records')
    elif request.method == 'POST' and 'company_submit' in request.form:
        main_facility = request.form.get('main_faci')
        carrier_type = request.form.get('carrier_type')
        country = request.form.get('country')
        cursor.execute("INSERT into company VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (C_NAME, EST_DATE, ADDRESS, FUNCTIONS[0], FUNCTIONS[1], main_facility, FUNCTIONS[2], carrier_type, country, FUNCTIONS[3],))
        mysql.connection.commit()
        return redirect('/records')

    return render_template('contribute.html')

if __name__ == "__main__":
    app.run(debug=True)