# import modules
# import atexit
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, Event
import pandas as pd
import plotly.graph_objs as go
import configparser as config
import pigpio as gpio
import DHT22
import pymysql as sql
import time
from multiprocessing import Process
import warnings
warnings.filterwarnings('ignore')


# read config file
def get_conf(file_name):
    get_conf.conf = config.ConfigParser()
    try:
        get_conf.conf.read(file_name)
    except config.ParsingError as e:
        quit(print(e))


# connect to database, create database and table if not exists
def sql_db_connect(host, user, passw, db_name, db_table):
    try:
        sql_db_connect.db = sql.connect(host, user, passw)
    except sql.err.OperationalError as e:
        quit(print(e))
    cursor = sql_db_connect.db.cursor()
    cursor.execute('CREATE DATABASE IF NOT EXISTS %s;' % db_name)
    cursor.execute('USE %s;' % db_name)
    cursor.execute('''CREATE TABLE IF NOT EXISTS %s (
        TIME INT NOT NULL,
        TEMP FLOAT(3, 1) NOT NULL,
        HUMID FLOAT(3, 1) NOT NULL)''' % db_table)


# setup temperature and humidity sensor
def setup_temp_humid(gpio_num):
    pi = gpio.pi()
    if not pi.connected:
        quit(clorox(''))
    setup_temp_humid.dht22 = DHT22.sensor(pi, gpio_num)
    setup_temp_humid.dht22.trigger()
    time.sleep(4)


# read temperature and humidity sensor, store reading in database, read database
def get_temp_humid(db_table, freq):
    while True:
        # setup_temp_humid.dht22.trigger()
        time.sleep(4)
        # temp = setup_temp_humid.dht22.temperature()
        # humid = setup_temp_humid.dht22.humidity()
        temp = 90
        humid = 90
        cursor = sql_db_connect.db.cursor()
        try:
            cursor.execute('INSERT INTO %s(TIME, TEMP, HUMID) VALUES (%d, %f, %f)' %
                           (db_table, time.time(), temp, humid))
        except sql.err.DataError as e:
            quit(clorox('Check if the DHT22 sensor is connected - ' + str(e)))
        sql_db_connect.db.commit()
        print('LOL')
        time.sleep(freq)


# query database
def query(db_select, db_table, limit):
    q = ('SELECT %s FROM %s ORDER BY TIME DESC LIMIT %i' % (db_select, db_table, limit))
    df = pd.read_sql(q, sql_db_connect.db)
    return df


# plot temperature and humidity on a graph using dash
def graph():
    data_dict = {'Temperature': 'TEMP', 'Humidity': 'HUMID'}
    app = dash.Dash()
    app.layout = html.Div([
        html.Div([
            html.H1('hydropi')]),
        dcc.Dropdown(id='data-name',
                     options=[{'label': s, 'value': s}
                              for s in data_dict.keys()],
                     value=['Temperature'], multi=True),
        html.Div(id='graphs'),
        dcc.Interval(id='update', interval=30000)],
        className='container')

    @app.callback(Output('graphs', 'children'),
                  [Input('data-name', 'value')],
                  events=[Event('update', 'interval')])
    def update_graph(data_names):
        graphs = []
        x_date_time = list()
        returned = query('TIME, TEMP, HUMID', get_conf.conf['DB']['DB_TABLE'], 10)
        print(list(returned.TIME))
        print(list(returned.TEMP))
        print(list(returned.HUMID))
        if not data_names:
            graphs.append(html.P('Select a graph'))
        else:
            for i in returned.TIME:
                x_date_time.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i)))
            for name in data_names:
                data = go.Scatter(x=x_date_time, y=list(returned.TEMP), mode='lines+markers')
                graphs.append(html.Div(dcc.Graph(
                    id=name, animate=True, figure={'data': [data], 'layout': go.Layout(title=name)})))
                print(name)
        return graphs

    if __name__ == '__main__':
        app.run_server(debug=True)


# cleanup function
def clorox(e):
    print(e)
    try:
        p.terminate()
    except NameError:
        pass
    sql_db_connect.db.close()


# load config
get_conf('config.ini')

# connect to database
sql_db_connect(get_conf.conf['DB']['HOST'], get_conf.conf['DB']['USER'], get_conf.conf['DB']['PASSW'],
               get_conf.conf['DB']['DB_NAME'], get_conf.conf['DB']['DB_TABLE'])

# setup DHT22 sensor
#try:
#    setup_temp_humid(int(get_conf.conf['SENSOR']['TEMP_HUMID_GPIO']))
#except ValueError as er:
#    quit(print('TEMP_HUMID_GPIO must be a number - ' + str(er)))

# start a process to run the get_temp_humid function
if __name__ == '__main__':
    try:
        p = Process(target=get_temp_humid,
                    args=(get_conf.conf['DB']['DB_TABLE'], int(get_conf.conf['SENSOR']['TEMP_HUMID_FREQ'])))
        p.start()
    except ValueError as er:
        quit(clorox('TEMP_HUMID_FREQ must be a number - ' + str(er)))

graph()

# atexit.register(clorox, e='end')