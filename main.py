from flask import Flask, request, render_template, redirect, url_for
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from google.cloud import firestore
from secret import secret, secret_key, usersdb
import json
from datetime import datetime


class User(UserMixin):
    def __init__(self, username):
        super().__init__()
        self.id = username
        self.username = username
        self.par = {}

app = Flask(__name__)
app.template_folder = 'templates'
app.config['SECRET_KEY'] = secret_key

login = LoginManager(app)
login.login_view = '/static/login.html'

usersdb = {
    'Marco':'mamei',
    'Chiara':'agostinelli',
    'Alessandra':'occhionero'
}

@login.user_loader
def load_user(username):
    if username in usersdb:
        return User(username)
    return None

@app.route('/')
def root():
    return redirect('/static/index.html')

@app.route('/main')
@login_required
def index():
    return render_template('main.html', username=current_user.username)

@app.route('/graph')
@login_required
def index1():
    return redirect('/static/graph.html')

@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('/main'))
    username = request.values['u']
    password = request.values['p']
    if username in usersdb and password == usersdb[username]:
        login_user(User(username))
        next_page = request.args.get('next')
        if not next_page:
            next_page = '/main'
        return redirect(next_page)
    return redirect('/static/login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@app.route('/farm/sensor',methods=['GET'])
def read_all():
    db =firestore.Client.from_service_account_json('credentials.json') #questo mi serve x farlo in locale
    #db = firestore.Client()
    data = []
    for doc in db.collection('sensor').stream():
        x = doc.to_dict()
        data.append([x['date'].split(' ')[0], float(x['maxT']),float(x['minT']), float(x['windSpeed']), float(x['humidity']), float(x['precipitation'])])
    return json.dumps(data)

########################  GRAFICI! ##########################################################################
@app.route('/Temperature',methods=['GET'])
@login_required
def graph():
    data = json.loads(read_all())
    data_temp = [['Date', 'MinT', 'MaxT']]
    for item in data:
        date = item[0]
        maxT = item[1]
        minT = item[2]
        data_temp.append([date, minT, maxT])
    return render_template('temperature.html', data=data_temp)

@app.route('/Windspeed',methods=['GET'])
@login_required
def graph1():
    data = json.loads(read_all())
    data_wind = [['Date', 'WindSpeed']]
    for item in data:
        date = item[0]
        windspeed = item[3]
        data_wind.append([date, windspeed])
    return render_template('windspeed.html', data = data_wind)

@app.route('/Humidity',methods=['GET'])
@login_required
def graph2():
    data = json.loads(read_all())
    data_hum = [['Date', 'Humidity']]
    for item in data:
        date = item[0]
        humidity = item[4]
        data_hum.append([date, humidity])
    return render_template('humidity.html', data = data_hum)

@app.route('/Precipitation',methods=['GET'])
@login_required
def graph3():
    data = json.loads(read_all())
    data_prep = [['Date', 'Precipitation']]
    for item in data:
        date = item[0]
        precipitation = item[5]
        data_prep.append([date, precipitation])
    return render_template('precipitation.html', data = data_prep)

########################################## FINE GRAFICI ####################################################################

@app.route('/farm/sensor/average', methods=['GET'])
def read_average():
    db = firestore.Client.from_service_account_json('credentials.json')
    #db = firestore.Client()
    data = []
    sum_values = {'maxT': 0, 'minT': 0, 'windSpeed': 0, 'humidity': 0, 'precipitation': 0}
    count = 0
    for doc in sorted(db.collection('sensor').stream(), key=lambda x: x.get('date'), reverse=True):
        x = doc.to_dict()
        date = datetime.strptime(x['date'], '%Y-%m-%d')
        if count % 7 == 0:
            if count > 0:
                data.append([last_date.strftime('%Y-%m-%d')] + [round(sum_values[key]/7, 2) for key in sum_values])
            sum_values = {'maxT': 0, 'minT': 0, 'windSpeed': 0, 'humidity': 0, 'precipitation': 0}
            last_date = date
        for key in sum_values:
            sum_values[key] += float(x[key])
        count += 1
    data.append([last_date.strftime('%Y-%m-%d')] + [round(sum_values[key]/7, 2) for key in sum_values])
    html = "<html><head>"
    html += "<meta http-equiv='refresh' content='5'>"
    html += "</head><body>"
    html += "<table align='center' style='border-collapse: collapse; border: 1px solid black; margin-top: 30px;'>"
    html += "<caption style='text-align: center; font-weight: bold; font-size: 24px;'>Maximum values reached</caption>"
    html += "<caption style='text-align: center; font-size: 16px;'>in the 7 days preceding the specified date</caption>"
    html += "<tr style='border: 1px solid black;'><th style='border: 1px solid black; padding: 5px;'>Date</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Max temperature</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Min temperature</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Wind speed</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Humidity</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Precipitation</th></tr>"
    for row in data:
        html += "<tr style='border: 1px solid black;'>"
        for item in row:
            html += "<td style='border: 1px solid black; padding: 5px; text-align: center;'>{}</td>".format(item)
        html += "</tr>"
    html += "</table>"
    return html


@app.route('/farm/sensor/minimum', methods=['GET'])
def read_minimum():
    db = firestore.Client.from_service_account_json('credentials.json')
    #db = firestore.Client()
    data = []
    min_values = {'maxT': float('inf'), 'minT': float('inf'), 'windSpeed': float('inf'), 'humidity': float('inf'),'precipitation': float('inf')}
    count = 0
    for doc in sorted(db.collection('sensor').stream(), key=lambda x: x.get('date'), reverse=True):
        x = doc.to_dict()
        date = datetime.strptime(x['date'], '%Y-%m-%d')
        if count % 7 == 0:
            if count > 0:
                data.append([last_date.strftime('%Y-%m-%d')] + list(min_values.values()))
            min_values = {'maxT': float('inf'), 'minT': float('inf'), 'windSpeed': float('inf'),'humidity': float('inf'), 'precipitation': float('inf')}
            last_date = date
        for key in min_values:
            if float(x[key]) < min_values[key]:
                min_values[key] = float(x[key])
        count += 1
    data.append([last_date.strftime('%Y-%m-%d')] + list(min_values.values()))
    html = "<html><head>"
    html += "<meta http-equiv='refresh' content='5'>"
    html += "</head><body>"
    html += "<table align='center' style='border-collapse: collapse; border: 1px solid black; margin-top: 30px;'>"
    html += "<caption style='text-align: center; font-weight: bold; font-size: 24px;'>Minimum values reached</caption>"
    html += "<caption style='text-align: center; font-size: 16px;'>in the 7 days preceding the specified date</caption>"
    html += "<tr style='border: 1px solid black;'><th style='border: 1px solid black; padding: 5px;'>Date</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Max temperature</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Min temperature</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Wind speed</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Humidity</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Precipitation</th></tr>"
    for row in data:
        html += "<tr style='border: 1px solid black;'>"
        for item in row:
            html += "<td style='border: 1px solid black; padding: 5px; text-align: center;'>{}</td>".format(item)
        html += "</tr>"
    html += "</table>"
    return html


@app.route('/farm/sensor/maximum', methods=['GET'])
def read_maximum():
    db = firestore.Client.from_service_account_json('credentials.json')
    #db = firestore.Client()
    data = []
    max_values = {'maxT': float('-inf'), 'minT': float('-inf'), 'windSpeed': float('-inf'), 'humidity': float('-inf'),'precipitation': float('-inf')}
    count = 0
    for doc in sorted(db.collection('sensor').stream(), key=lambda x: x.get('date'), reverse=True):
        x = doc.to_dict()
        date = datetime.strptime(x['date'], '%Y-%m-%d')
        if count % 7 == 0:
            if count > 0:
                data.append([last_date.strftime('%Y-%m-%d')] + list(max_values.values()))
            max_values = {'maxT': float('-inf'), 'minT': float('-inf'), 'windSpeed': float('-inf'),'humidity': float('-inf'), 'precipitation': float('-inf')}
            last_date = date
        for key in max_values:
            if float(x[key]) > max_values[key]:
                max_values[key] = float(x[key])
        count += 1
    data.append([last_date.strftime('%Y-%m-%d')] + list(max_values.values()))
    html = "<html><head>"
    html += "<meta http-equiv='refresh' content='5'>"
    html += "</head><body>"
    html += "<table align='center' style='border-collapse: collapse; border: 1px solid black; margin-top: 30px;'>"
    html += "<caption style='text-align: center; font-weight: bold; font-size: 24px;'>Average values reached</caption>"
    html += "<caption style='text-align: center; font-size: 16px;'>in the 7 days preceding the specified date</caption>"
    html += "<tr style='border: 1px solid black;'><th style='border: 1px solid black; padding: 5px;'>Date</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Max temperature</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Min temperature</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Wind speed</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Humidity</th>"
    html += "<th style='border: 1px solid black; padding: 5px;'>Precipitation</th></tr>"
    for row in data:
        html += "<tr style='border: 1px solid black;'>"
        for item in row:
            html += "<td style='border: 1px solid black; padding: 5px; text-align: center;'>{}</td>".format(item)
        html += "</tr>"
    html += "</table>"
    return html

@app.route('/farm/sensor',methods=['POST'])
def save_data():
    s = request.values['secret']
    if s == secret:
        d = request.values['date'].split(' ')[0]
        maxT = request.values['maxT']
        minT = request.values['minT']
        windSpeed = request.values['windSpeed']
        humidity = request.values['humidity']
        precipitation = request.values['precipitation']
        db = firestore.Client.from_service_account_json('credentials.json')
        #db = firestore.Client()
        db.collection('sensor').document(d).set({'date': d, 'maxT': maxT, 'minT': minT, 'windSpeed': windSpeed, 'humidity': humidity, 'precipitation': precipitation})
        return 'ok', 200
    else:
        return 'Utente non autorizzato, impossibile accedere al sito', 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1880, debug=True)














