from flask import Flask, render_template, redirect, request, session, url_for
from flask_session import Session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import sys
from datetime import datetime
import random
import string
import base64
import copy

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'vivifica'

mysql = MySQL(app)

TEMP = None
DICT = None

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
                cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s)', (username, password, email, 0))
                mysql.connection.commit()
                cursor.execute('SELECT * FROM account WHERE username = %s', (username,))
                account = cursor.fetchone()
                session['loggedin'] = True
                session['username'] = account['username']
                session['isAdmin'] = 0
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
    session['isAdmin'] = None
    return redirect("/")

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

@app.route("/records", methods=["GET","POST"])
def records():
    checkUser()
    if not session.get("username"): 
        return redirect("/login")
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT reg_num FROM aircraft')
    aircrafts = cursor.fetchall()
    if request.method == 'POST' and "contribute" in request.form:
        return redirect('/contribute')
    elif request.method == 'POST' and 'adminify' in request.form:
        cursor.execute('UPDATE account set isAdmin = 1 WHERE username = %s', (session['username'],))
        mysql.connection.commit()
        return redirect('/records')
    elif request.method == 'POST' and 'aircraft_report' in request.form:
        reg_num = request.form.get('aircraft_report')
        cursor.execute('SELECT * FROM aircraft WHERE reg_num = %s', (reg_num,))
        aircraft = cursor.fetchone()
        cursor.execute('SELECT * FROM aircraft_type WHERE aircraft_name = %s', (aircraft['aircraft_name'],))
        type = cursor.fetchone()
        cursor.execute('SELECT * FROM aircraft_parts LEFT JOIN part on aircraft_parts.part_id = part.part_id WHERE aircraft_name = %s', (type['aircraft_name'],))
        type_parts = cursor.fetchall()
        cursor.execute('SELECT * FROM options WHERE reg_num = %s', (reg_num,))
        options = cursor.fetchall()
        cursor.execute('SELECT * FROM delivery WHERE reg_num = %s', (reg_num,))
        deliveries = cursor.fetchall()
        cursor.execute('call generateFullMaintenanceRecord(%s)', (reg_num,))
        full_records = cursor.fetchall()
        cursor.execute('call generateFullReplacedParts(%s)', (reg_num,))
        replaced_parts = cursor.fetchall()
        return render_template('full_aircraft_report.html', aircraft=aircraft, type=type, type_parts=type_parts, options=options, deliveries=deliveries, full_records=full_records, replaced_parts=replaced_parts)
    return render_template("records.html", aircrafts=aircrafts)

@app.route("/bye")
def bye():
    return render_template("bye.html")

@app.route("/parts", methods = ["GET", "POST"])
def parts():
    checkUser()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute('SELECT * FROM part ORDER BY p_name ASC')
    parts = cursor.fetchall()
    cursor.execute('SELECT c_name FROM company')
    data = cursor.fetchall()
    cursor.execute('SELECT * from avionics')
    avionics = cursor.fetchall()
    cursor.execute('SELECT * from engine')
    engines = cursor.fetchall()
    cursor.execute('SELECT * from wing')
    wings = cursor.fetchall()
    cursor.execute('SELECT max(cost) as max_cost FROM part')
    cost_max = cursor.fetchone()
    cursor.execute('SELECT min(cost) as min_cost FROM part')
    cost_min = cursor.fetchone()


    if request.method == 'POST' and 'query' in request.form:
        query = request.form.get('query')
        min = request.form.get('cost_display')
        print(min)
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

        #cursor.execute('SELECT * FROM part WHERE p_name LIKE %s  or c_name LIKE %s' + list, ['%%' + query + '%%', '%%' + query + '%%'])
        cursor.execute('call searchParts(%s, %s)', (query,min))
        
        table = None
        if request.form.getlist('check'):
            table = 'true'
        
        return render_template("parts.html", parts=cursor.fetchall(), search="true", table=table, data=data, avionics=avionics, engines=engines, wings=wings, query=query, cost_min=cost_min, cost_max=cost_max)

    elif request.method == 'POST' and 'modalfunc' in request.form:
        p_id = request.form.get('modalfunc')[1:]
        val = request.form['ps']
        cursor.execute('DELETE FROM part where part_id = %s', (p_id,))
        mysql.connection.commit()
        return redirect('/parts')

    elif request.method == 'POST' and 'update' in request.form:
        p_name = request.form.get('p_name')
        c_name = request.form.get('company')
        cost = request.form.get('cost')
        part_id = request.form.get('key')
        cursor.execute('UPDATE part SET p_name = %s, c_name = %s, cost = %s WHERE part_id = %s', (p_name, c_name, cost, part_id,))
        mysql.connection.commit()
        classification = request.form.get('classification')
        if classification == 'Avionics':
            type = request.form.get('type')
            cursor.execute('UPDATE avionics SET classification = %s WHERE part_id = %s', (type, part_id,))
            mysql.connection.commit()
        elif classification == 'Engine':
            weight = request.form.get('weight')
            thrust = request.form.get('thrust')
            bypass = request.form.get('bypass')
            cursor.execute('UPDATE engine SET weight = %s, thrust = %s, bypass = %s WHERE part_id = %s', (weight, thrust, bypass, part_id,))
            mysql.connection.commit()
        elif classification == 'Wing':
            material = request.form.get('material')
            span = request.form.get('span')
            cursor.execute('UPDATE wing SET material = %s, span = %s WHERE part_id = %s', (material, span, part_id,))
            mysql.connection.commit()
        return redirect('/parts')

    return render_template("parts.html", parts=parts, data=data, avionics=avionics, engines=engines, wings=wings, cost_min=cost_min, cost_max=cost_max)

@app.route("/aircraft", methods = ["GET", "POST"])
def aircraft():
    checkUser()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM aircraft ORDER BY reg_num asc')
    aircrafts = cursor.fetchall()
    cursor.execute('SELECT aircraft_name FROM aircraft_type')
    data = cursor.fetchall()
    cursor.execute('SELECT c_name FROM company WHERE is_airline = 1')
    airlines = cursor.fetchall()

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

        return render_template("aircraft.html", aircrafts=cursor.fetchall(), search="true", table=table, data=data, airlines=airlines, query=query)

    elif request.method == 'POST' and 'update' in request.form:
        reg_num = request.form.get('name')
        type = request.form.get('model')
        date = request.form.get('date')
        site = request.form.get('site')
        cursor.execute('UPDATE aircraft set aircraft_name = %s, produce_date = %s, production_site = %s WHERE reg_num = %s', (type, date, site, reg_num,))
        mysql.connection.commit()
        return redirect('/aircraft')

    elif request.method == 'POST' and 'modalfunc' in request.form:
        reg_num = request.form.get('modalfunc')[1:]
        val = request.form.get('ac')
        if val == 'delete':
            cursor.execute('DELETE FROM aircraft where reg_num = %s', (reg_num,))
            mysql.connection.commit()
            return redirect('/aircraft')

    elif request.method == 'POST' and 'aircraft_functions' in request.form:
        reg_num = request.form.get('aircraft_functions')[1:]
        val = request.form.get('ac')
        if val == 'maintenance':
            cursor.execute('SELECT * from maintenance WHERE reg_num = %s ORDER BY date DESC', (reg_num,))
            maintenance = cursor.fetchall()
            return render_template('aircraft_report.html', maintenance=maintenance, reg_num=reg_num)
        elif val == 'deliveries':
            cursor.execute('SELECT * from delivery where reg_num = %s ORDER BY delivery_date DESC', (reg_num,))
            deliveries = cursor.fetchall()
            cursor.execute('SELECT c_name FROM company WHERE is_airline = 1')
            airlines = cursor.fetchall()
            return render_template('aircraft_deliveries.html', reg_num=reg_num, deliveries=deliveries, airlines=airlines)
        elif val == 'options':
            cursor.execute('SELECT * from options where reg_num = %s ORDER BY opt_name ASC', (reg_num,))
            options = cursor.fetchall()
            return render_template('aircraft_options.html', reg_num=reg_num, options=options)

    return render_template("aircraft.html", aircrafts=aircrafts, data=data, airlines=airlines)

@app.route("/maintenance", methods = ["GET", "POST"])
def maintenance():
    checkUser()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM maintenance ORDER BY date DESC')
    records = cursor.fetchall()
    cursor.execute('SELECT c_name FROM company WHERE is_maintenance = 1')
    data = cursor.fetchall()
    cursor.execute('SELECT reg_num FROM aircraft')
    data2 = cursor.fetchall()
    cursor.execute('SELECT * from a_check')
    a_checks = cursor.fetchall()
    cursor.execute('SELECT * from c_check')
    c_checks = cursor.fetchall()
    cursor.execute('SELECT * from d_check')
    d_checks = cursor.fetchall()

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
        
        cursor.execute('SELECT * FROM maintenance WHERE c_name LIKE %s or facility_loc LIKE %s or reg_num LIKE %s' + list, ['%%' + query + '%%', '%%' + query + '%%', '%%' + query + '%%'])
        table = None
        if request.form.getlist('check'):
            table = 'true'
        return render_template("maintenance.html", records=cursor.fetchall(), search="true", table=table, data=data, data2=data2, a_checks=a_checks, c_checks=c_checks, d_checks=d_checks, query=query)

    elif request.method == 'POST' and 'modalfunc' in request.form:
        m_id = request.form.get('modalfunc')[1:]
        func = request.form.get('mt')
        if func == 'delete':
            cursor.execute('DELETE FROM maintenance WHERE maintenance_id = %s', (m_id,))
            mysql.connection.commit()
            return redirect('/maintenance')

    elif request.method == 'POST' and 'maintenance_functions' in request.form:
        m_id = request.form.get('maintenance_functions')[1:]
        cursor.execute('SELECT * FROM maintenance WHERE maintenance_id = %s', (m_id,))
        maint = cursor.fetchone()
        cursor.execute('WITH t as (SELECT part_id, qty FROM replaced_parts natural join maintenance WHERE maintenance_id = %s) SELECT part_id, p_name, qty FROM t natural join part', (m_id,))
        parts = cursor.fetchall()
        return render_template('maintenance_parts.html', maint=maint, parts=parts)


    elif request.method == 'POST' and 'update' in request.form:
        m_id = request.form.get('key')
        date = request.form.get('date')
        c_name = request.form.get('company')
        facility_loc = request.form.get('facility_loc')
        summary = request.form.get('summary')
        reg_num = request.form.get('reg_num')
        cursor.execute('UPDATE maintenance set c_name = %s, date = %s, facility_loc = %s, summary = %s, reg_num = %s WHERE maintenance_id = %s', (c_name, date, facility_loc, summary, reg_num, m_id))
        if 'wing_check' in request.form:
            flap_test = request.form.get('flap_test')
            brake_test = request.form.get('brake_test')
            damage_check = request.form.get('damage_check')
            oxy_pres_check = request.form.get('oxy_pres_check')
            cursor.execute('UPDATE a_check set flap_test = %s, brake_test = %s, damage_check = %s, oxy_pres_check = %s WHERE maintenance_id = %s', (flap_test, brake_test, damage_check, oxy_pres_check, m_id,))
            mysql.connection.commit()
        if 'door_check' in request.form:
            door_check = request.form.get('door_check')
            engine_check = request.form.get('engine_check')
            fuel_pres_check = request.form.get('fuel_pres_check')
            cursor.execute('UPDATE c_check set door_check = %s, engine_check = %s, fuel_pres_check = %s WHERE maintenance_id = %s', (door_check, engine_check, fuel_pres_check, m_id,))
            mysql.connection.commit()
        if 'flap_test' in request.form:
            wing_check = request.form.get('wing_check')
            floor_check = request.form.get('floor_check')
            stab_check = request.form.get('stab_check')
            cursor.execute('UPDATE d_check set wing_check = %s, floor_check = %s, stab_check = %s WHERE maintenance_id = %s', (wing_check, floor_check, stab_check, m_id,))
            mysql.connection.commit()
        return redirect('/maintenance')

    return render_template("maintenance.html", records=records, data=data, data2=data2, a_checks=a_checks, c_checks=c_checks, d_checks=d_checks)

@app.route("/company", methods = ["GET", "POST"])
def company():
    checkUser()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM company ORDER BY c_name ASC')
    companies = cursor.fetchall()
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
        return render_template("company.html", companies=cursor.fetchall(), search="true", table=table, query=query)

    elif request.method == 'POST' and 'modalfunc' in request.form:
        c_id = request.form.get('modalfunc')[1:]
        cursor.execute('DELETE from company WHERE c_id = %s', (c_id,))
        mysql.connection.commit()
        return redirect('/company')

    elif request.method == 'POST' and 'update' in request.form:
        c_id = request.form.get('key')
        c_name = request.form.get('c_name')
        est_date = request.form.get('est_date')
        address = request.form.get('address')
        main_facility = request.form.get('main_faci')
        carrier_type = request.form.get('carrier_type')
        country = request.form.get('country')
        cursor.execute('UPDATE company set c_name = %s, est_date = %s, address = %s, main_facility = %s, carrier_type = %s, country = %s WHERE c_id = %s', (c_name, est_date, address, main_facility, carrier_type, country, c_id,))
        mysql.connection.commit()
        return redirect('/company')
            
    return render_template("company.html", companies=companies)

@app.route("/type", methods = ["GET", "POST"])
def type():
    checkUser()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM aircraft_type ORDER BY aircraft_name ASC')
    types = cursor.fetchall()
    cursor.execute('SELECT c_name FROM company WHERE is_manufacturer = 1')
    data = cursor.fetchall()

    if request.method == 'POST' and 'query' in request.form:
        query = request.form.get('query')

        val = request.form.get('sort')
        if val == '1':
            list = 'ORDER BY aircraft_name ASC'
        elif val == '2':
            list = 'ORDER BY aircraft_name DESC'
        elif val == '3':
            list = 'ORDER BY c_name ASC'
        elif val == '4':
            list = 'ORDER BY c_name DESC'

        cursor.execute('SELECT * FROM aircraft_type WHERE c_name LIKE %s or aircraft_name LIKE %s' + list, ['%%' + query + '%%', '%%' + query + '%%'])
        table = None
        if request.form.getlist('check'):
            table = 'true'
        return render_template("type.html", types=cursor.fetchall(), search="true", table=table, data=data, query=query)

    elif request.method == 'POST' and 'update' in request.form:
        t_id = request.form.get('key')
        type_name = request.form.get('name')
        c_name = request.form.get('manu')
        year = request.form.get('year')
        engines = request.form.get('engines')
        size = request.form.get('size')
        cursor.execute('UPDATE aircraft_type SET aircraft_name = %s, c_name = %s, year_introduced = %s, no_engines = %s, size_class = %s WHERE type_id = %s', (type_name, c_name, year, engines, size, t_id,))
        mysql.connection.commit()
        return redirect('/type')

    elif request.method == 'POST' and 'modalfunc' in request.form:
        t_id = request.form.get('modalfunc')[1:]
        func = request.form.get('ty')
        if func == 'delete':
            cursor.execute('DELETE FROM aircraft_type WHERE type_id = %s', (t_id,))
            mysql.connection.commit()
            return redirect('/type')
        elif func == 'parts':
            cursor.execute('with t as (SELECT part_id, qty from aircraft_parts natural join aircraft_type WHERE type_id = %s) SELECT part_id, p_name, qty FROM t natural join part', (t_id,))
            parts = cursor.fetchall()
            cursor.execute('SELECT aircraft_name FROM aircraft_type WHERE type_id = %s', (t_id,))
            type = cursor.fetchone()
            return render_template('type_parts.html', parts=parts, t_id=t_id, type=type)
    
    return render_template("type.html", types=types, data=data)

@app.route('/contribute', methods=['GET', 'POST'])
def contribute():
    checkUser()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    global TEMP, DICT
    if not session.get("username"): 
        return redirect("/login")

    if request.method == 'POST' and 'adminify' in request.form:
        cursor.execute('UPDATE account set isAdmin = 1 WHERE username = %s', (session['username'],))
        mysql.connection.commit()
        return redirect('/records')

    if request.method == 'POST' and "part_1" in request.form:
        val = request.form.get('next')
        data = None
        data2 = None
        if val == '1':
            cursor.execute('SELECT c_name FROM company WHERE is_manufacturer = 1')
            data = cursor.fetchall()
        elif val == '2':
            cursor.execute('SELECT aircraft_name FROM aircraft_type')
            data = cursor.fetchall()
        elif val == '3':
            cursor.execute('SELECT c_name FROM company WHERE is_supplier = 1')
            data = cursor.fetchall()
        elif val == '4':
            cursor.execute('SELECT c_name FROM company where is_maintenance = 1')
            data = cursor.fetchall()
            cursor.execute('SELECT reg_num from aircraft')
            data2 = cursor.fetchall()
        return render_template('contribute.html', val=val, data=data, data2=data2)

    if request.method == 'POST' and "type_submit" in request.form:
        t_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 20))
        name = request.form.get('name')
        company = request.form.get('manu')
        year = request.form.get('year')
        engines = request.form.get('engines')
        size = request.form.get('size')
        TEMP = {'t_id': t_id, 'name': name, 'c_name': company, 'year': year, 'engines': engines, 'size': size}
        cursor.execute('SELECT p_name FROM part')
        parts = cursor.fetchall()
        return render_template('contribute.html', val='1b', parts=parts)

    elif request.method == 'POST' and "type_p2_submit" in request.form:
        a_name = TEMP['name']
        cursor.execute('INSERT into aircraft_type VALUES (%s, %s, %s, %s, %s, %s)', (TEMP['t_id'], TEMP['name'], TEMP['c_name'], TEMP['year'], TEMP['size'], TEMP['engines'],))
        mysql.connection.commit()
        for key in DICT:
            val = DICT[key]
            if len(key) % 4 == 2:
                key = key + '=='
            elif len(key) % 4 == 3:
                key = key + '='
            key = base64.b64decode(key)
            cursor.execute('SELECT part_id FROM part WHERE p_name = %s', (key,))
            p_id = cursor.fetchone()['part_id']
            cursor.execute('INSERT into aircraft_parts VALUES (%s, %s, %s)', (a_name, p_id, val,))
            mysql.connection.commit()
        return redirect('/type')

    elif request.method == 'POST' and "aircraft_submit" in request.form:
        reg_num = request.form.get('name').replace(' ', '-')
        model = request.form.get('model')
        date = datetime.strptime(request.form.get('date'),'%Y-%m-%d')
        site = request.form.get('site')
        cursor.execute("INSERT into aircraft VALUES (%s, %s, %s, %s)", (reg_num, model, date, site,))
        mysql.connection.commit()
        return redirect('/aircraft')
        
    elif request.method == 'POST' and 'part_submit' in request.form:
        p_name = request.form.get('p_name')
        c_name = request.form.get('company')
        cost = request.form.get('cost')
        subclass = request.form.get('classification')
        p_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 20))
        TEMP = {'p_id': p_id, 'p_name': p_name, 'c_name': c_name, 'cost': cost}
        if subclass == 'Other':
            cursor.execute('INSERT into part VALUES(%s, %s, %s, %s)', (p_id, p_name, c_name, cost,))
            mysql.connection.commit()
            return redirect('/parts')
        else:
            return render_template('contribute.html', val='3b', subclass=subclass)

    elif request.method == 'POST' and 'part_p2_submit' in request.form:
        p_id = TEMP['p_id']
        cursor.execute('INSERT into part VALUES (%s, %s, %s, %s)', (TEMP['p_id'], TEMP['p_name'], TEMP['c_name'], TEMP['cost'],))
        mysql.connection.commit()
        if 'classification' in request.form:
            classification = request.form.get('classification')
            cursor.execute("INSERT into avionics VALUES (%s, %s)", (p_id, classification,))
            mysql.connection.commit()
        elif 'weight' in request.form:
            weight = request.form.get('weight')
            thrust = request.form.get('thrust')
            bypass = request.form.get('bypass')
            cursor.execute('INSERT into engine VALUES (%s, %s, %s, %s)', (p_id, weight, thrust, bypass,))
            mysql.connection.commit()
        elif 'material' in request.form:
            material = request.form.get('material')
            span = request.form.get('span')
            cursor.execute('INSERT into wing VALUES (%s, %s, %s)', (p_id, material, span,))
            mysql.connection.commit()
        return redirect('/parts')

    elif request.method == 'POST' and 'maintenance_submit' in request.form:
        m_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 20))
        c_name = request.form.get('company')
        date = datetime.strptime(request.form.get('date'),'%Y-%m-%d')
        facility_loc = request.form.get('facility_loc')
        summary = request.form.get('summary')
        reg_num = request.form.get('reg_num')
        TEMP = {'m_id': m_id, 'c_name': c_name, 'date': date, 'facility_loc': facility_loc, 'summary': summary, 'reg_num': reg_num}
        check = request.form.get('check')
        cursor.execute('SELECT p_name from part')
        parts = cursor.fetchall()
        return render_template('contribute.html', val='4b', check=check, parts=parts)

    elif request.method == 'POST' and 'maintenance_p2_submit' in request.form:
        m_id = TEMP['m_id']
        cursor.execute("INSERT into maintenance VALUES (%s, %s, %s, %s, %s, %s)", (m_id, TEMP['c_name'], TEMP['date'], TEMP['facility_loc'], TEMP['summary'], TEMP['reg_num'],))
        mysql.connection.commit()
        if 'flap_test' in request.form:
            flap_test = request.form.get('flap_test')
            brake_test = request.form.get('brake_test')
            damage_check = request.form.get('damage_check')
            oxy_pres_check = request.form.get('oxy_pres_check')
            cursor.execute('INSERT into a_check VALUES(%s, %s, %s, %s, %s)', (m_id, flap_test, brake_test, damage_check, oxy_pres_check,))
            mysql.connection.commit()
        if 'door_check' in request.form:
            door_check = request.form.get('door_check')
            engine_check = request.form.get('engine_check')
            fuel_pres_check = request.form.get('fuel_pres_check')
            cursor.execute('INSERT into c_check VALUES(%s, %s, %s, %s)', (m_id, door_check, engine_check, fuel_pres_check,))
            mysql.connection.commit()
        if 'flap_test' in request.form:
            wing_check = request.form.get('wing_check')
            floor_check = request.form.get('floor_check')
            stab_check = request.form.get('stab_check')
            cursor.execute('INSERT into d_check VALUES(%s, %s, %s, %s)', (m_id, wing_check, floor_check, stab_check,))
            mysql.connection.commit()
        for key in DICT:
            val = DICT[key]
            if len(key) % 4 == 2:
                key = key + '=='
            elif len(key) % 4 == 3:
                key = key + '='
            name = base64.b64decode(key).decode()
            cursor.execute('SELECT * FROM part WHERE p_name = %s', (name,))
            part = cursor.fetchone()
            cursor.execute('INSERT into replaced_parts VALUES (%s, %s, %s)', (m_id, part['part_id'], val,))
            mysql.connection.commit()
        return redirect('/maintenance')

    elif request.method == 'POST' and 'company_next' in request.form:
        c_name = request.form.get('c_name')
        est_date = request.form.get('est_date')
        address = request.form.get('address')
        isProvider = int(str(request.form.get('provider')).replace('None', '0').replace('on', '1'))
        isManufacturer = int(str(request.form.get('manufacturer')).replace('None', '0').replace('on', '1'))
        isSupplier = int(str(request.form.get('supplier')).replace('None', '0').replace('on', '1'))
        isAirline = int(str(request.form.get('airline')).replace('None', '0').replace('on', '1'))
        c_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 20))
        TEMP = {'c_id': c_id, 'c_name': c_name, 'est_date': est_date, 'address': address, 'isProvider': isProvider, 'isManufacturer': isManufacturer, 'isSupplier': isSupplier, 'isAirline': isAirline}
        if isManufacturer == 1 or isAirline == 1:
            return render_template('contribute.html', val='5b', isManufacturer=isManufacturer, isAirline=isAirline)
        else: 
            cursor.execute("INSERT into company VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (c_id, c_name, est_date, address, isProvider, isManufacturer, None, isAirline, None, None, isSupplier,))
            mysql.connection.commit()
            return redirect('/company')

    elif request.method == 'POST' and 'company_submit' in request.form:
        c_id = TEMP['c_id']
        main_facility = request.form.get('main_faci')
        carrier_type = request.form.get('carrier_type')
        country = request.form.get('country')
        cursor.execute("INSERT into company VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (c_id, TEMP['c_name'], TEMP['est_date'], TEMP['address'], TEMP['isProvider'], TEMP['isManufacturer'], main_facility, TEMP['isAirline'], carrier_type, country, TEMP['isSupplier'],))
        mysql.connection.commit()
        return redirect('/company')

    return render_template('contribute.html')

@app.route('/postmethod', methods = ['POST'])
def js_post():
    global DICT
    DICT = request.form.to_dict()
    return 'transformed'

@app.route('/manageDelivery', methods=['POST'])
def manageDelivery():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    arr = request.form.to_dict()
    reg_num = arr['reg_num']
    name = arr['name']
    date = arr['date']
    func = arr['type']
    if func == 'delete':
        cursor.execute('DELETE FROM delivery WHERE reg_num = %s and airline_name = %s and delivery_date = %s', (reg_num, name, date,))
        mysql.connection.commit()
    elif func == 'add':
        cursor.execute('INSERT into delivery VALUES (%s, %s, %s)', (reg_num, name, date,))
        mysql.connection.commit()
    return 'transaction completed'

@app.route('/manageOption', methods=['POST'])
def manageOption():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    arr = request.form.to_dict()
    reg_num = arr['reg_num']
    option = arr['option']
    func = arr['func']
    if func == 'delete':
        cursor.execute('DELETE FROM options WHERE reg_num = %s and opt_name = %s', (reg_num, option,))
        mysql.connection.commit()
    else:
        cursor.execute('INSERT into options VALUES (%s, %s)', (reg_num, option))
        mysql.connection.commit()
    return 'transaction completed'

def checkUser():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    print(session.get('username'))
    print(session.get('isAdmin'))
    if not session.get('username'):
        return redirect('/login')
    else: 
        cursor.execute('SELECT * FROM account WHERE username = %s', (session.get('username'),))
        user = cursor.fetchone()
        session['isAdmin'] = user['isAdmin']
if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=True)