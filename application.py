from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import sys
from datetime import datetime
import random
import string
import json

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

    cursor.execute('SELECT * FROM part')
    parts = cursor.fetchall()
    cursor.execute('SELECT c_name FROM company')
    data = cursor.fetchall()
    cursor.execute('SELECT * from avionics')
    avionics = cursor.fetchall()
    cursor.execute('SELECT * from engine')
    engines = cursor.fetchall()
    cursor.execute('SELECT * from wing')
    wings = cursor.fetchall()


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
        
        return render_template("parts.html", parts=cursor.fetchall(), search="true", table=table, data=data, avionics=avionics, engines=engines, wings=wings)

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

    return render_template("parts.html", parts=parts, data=data, avionics=avionics, engines=engines, wings=wings)

@app.route("/aircraft", methods = ["GET", "POST"])
def aircraft():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM aircraft')
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

        return render_template("aircraft.html", aircrafts=cursor.fetchall(), search="true", table=table, data=data, airlines=airlines)

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
        elif val == 'report':
            cursor.execute('SELECT * from maintenance WHERE reg_num = %s', (reg_num,))
            maintenance = cursor.fetchall()
            cursor.execute('SELECT * from delivery where reg_num = %s', (reg_num,))
            deliveries = cursor.fetchall()
            cursor.execute('SELECT * from options where reg_num = %s', (reg_num,))
            options = cursor.fetchall()
            return render_template('aircraft_report.html', maintenance=maintenance, deliveries=deliveries, options=options, reg_num=reg_num)

    return render_template("aircraft.html", aircrafts=aircrafts, data=data, airlines=airlines)

@app.route("/maintenance", methods = ["GET", "POST"])
def maintenance():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM maintenance')
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
        return render_template("maintenance.html", records=cursor.fetchall(), search="true", table=table, data=data, data2=data2, a_checks=a_checks, c_checks=c_checks, d_checks=d_checks)

    elif request.method == 'POST' and 'modalfunc' in request.form:
        m_id = request.form.get('modalfunc')[1:]
        cursor.execute('DELETE FROM maintenance where maintenance_id = %s', (m_id,))
        mysql.connection.commit()
        return redirect('/maintenance')

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
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM company')
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
        return render_template("company.html", companies=cursor.fetchall(), search="true", table=table)

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
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM aircraft_type')
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
        return render_template("type.html", types=cursor.fetchall(), search="true", table=table, data=data)

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
        cursor.execute('DELETE FROM aircraft_type WHERE type_id = %s', (t_id,))
        mysql.connection.commit()
        return redirect('/type')
    
    return render_template("type.html", types=types, data=data)

@app.route('/contribute', methods=['GET', 'POST'])
def contribute():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    global TEMP, DICT
    if not session.get("username"): 
        return redirect("/login")
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
        print(DICT)
        for key in DICT:
            val = DICT[key]
            key = key.replace('__','-')
            cursor.execute('SELECT part_id FROM part WHERE p_name = %s', (key,))
            p_id = cursor.fetchone()['part_id']
            print(p_id, file=sys.stdout)
            cursor.execute('INSERT into aircraft_parts VALUES (%s, %s, %s)', (a_name, p_id, val,))
            mysql.connection.commit()
        return redirect('/type')

    elif request.method == 'POST' and "aircraft_submit" in request.form:
        name = request.form.get('name').replace(' ', '-')
        model = request.form.get('model')
        date = datetime.strptime(request.form.get('date'),'%Y-%m-%d')
        site = request.form.get('site')
        TEMP = {'reg_num': name, 'model': model, 'prod_date': date, 'prod_site': site}
        cursor.execute('SELECT c_name FROM company WHERE is_airline = 1')
        return render_template('contribute.html', val = '2b', airlines=cursor.fetchall())
        
    elif request.method == 'POST' and 'aircraft_p2_submit' in request.form:
        reg_num = TEMP['reg_num']
        cursor.execute("INSERT into aircraft VALUES (%s, %s, %s, %s, %s)", (reg_num, TEMP['model'], TEMP['prod_date'], TEMP['prod_site'],))
        mysql.connection.commit()
        deliveries = request.form.get('deliveries').split('\r\n')
        print(deliveries, file=sys.stdout)
        for delivery in deliveries:
            tokens = delivery.split(',')
            print(tokens, file=sys.stdout)
            airline = tokens[0]
            if len(tokens) > 1:
                date = datetime.strptime(tokens[1], '%Y-%m-%d')
                cursor.execute('INSERT into delivery VALUES (%s, %s, %s)', (reg_num, airline, date,))
                mysql.connection.commit()
        options = request.form.get('options').split('\n')
        for option in options:
            if len(option) > 0:
                cursor.execute('INSERT into options VALUES (%s, %s)', (reg_num, option))
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
            return redirect('/records')

    elif request.method == 'POST' and 'company_submit' in request.form:
        main_facility = request.form.get('main_faci')
        carrier_type = request.form.get('carrier_type')
        country = request.form.get('country')
        cursor.execute("INSERT into company VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (c_id, c_name, est_date, address, isProvider, isManufacturer, main_facility, isAirline, carrier_type, country, isSupplier,))
        mysql.connection.commit()
        return redirect('/records')

    return render_template('contribute.html')

@app.route('/postmethod', methods = ['POST'])
def js_post():
    global DICT
    DICT = request.form.to_dict()
    print(DICT, file=sys.stdout)
    return 'transformed'

if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=True)