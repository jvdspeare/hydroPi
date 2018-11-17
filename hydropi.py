# import modules
# import atexit
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Event
import pandas as pd
import plotly.graph_objs as go
import configparser as config
import pigpio as gpio
import DHT22
import pymysql as sql
import time
from multiprocessing import Process, Queue
import warnings
warnings.filterwarnings('ignore')


# load config file
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


# take temperature and humidity reading then store data in database
def get_temp_humid(db_table, freq, g_time, g_temp):
    while True:
        setup_temp_humid.dht22.trigger()
        time.sleep(4)
        temp = setup_temp_humid.dht22.temperature()
        humid = setup_temp_humid.dht22.humidity()
        cursor = sql_db_connect.db.cursor()
        try:
            cursor.execute('INSERT INTO %s(TIME, TEMP, HUMID) VALUES (%d, %f, %f)' % (db_table, time.time(), temp, humid))
        except sql.err.DataError as e:
            quit(clorox('Check if the DHT22 sensor is connected - ' + str(e)))
        sql_db_connect.db.commit()
        query = ('SELECT TIME, TEMP, HUMID FROM %s' % db_table)
        df = pd.read_sql(query, sql_db_connect.db)
        g_time.put(df.TIME)
        g_temp.put(df.TEMP)
        time.sleep(freq)


# plot temperature and humidity on a graph using dash
def graph():
    app = dash.Dash()
    app.layout = html.Div(children=[
        html.H1('hydropi'),
        dcc.Graph(id='Temperature', animate=True),
        dcc.Interval(id='update', interval=5000)
    ])

    @app.callback(Output('Temperature', 'figure'),
                  events=[Event('update', 'interval')])
    def update_graph():
        data = go.Scatter(
            x=list(g_time.get()),
            y=list(g_temp.get()),
            name='scatter',
            mode='lines+markers'
        )

        return {'data': [data]}

    if __name__ == '__main__':
        app.run_server()


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
try:
    setup_temp_humid(int(get_conf.conf['SENSOR']['TEMP_HUMID_GPIO']))
except ValueError as er:
    quit(print('TEMP_HUMID_GPIO must be a number - ' + str(er)))

# start a process to run the get_temp_humid function, this will take temperature and humidity readings every x time
if __name__ == '__main__':
    g_time = Queue()
    g_temp = Queue()
    try:
        p = Process(target=get_temp_humid,
                    args=(get_conf.conf['DB']['DB_TABLE'], int(get_conf.conf['SENSOR']['TEMP_HUMID_FREQ']),
                          g_time, g_temp))
        p.start()
    except ValueError as er:
        quit(clorox('TEMP_HUMID_FREQ must be a number - ' + str(er)))

# start dash
graph()

# atexit.register(clorox, e='end')
