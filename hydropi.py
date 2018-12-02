# welcome message
print('''
 _               _          ______ _ 
| |             | |         | ___ (_)
| |__  _   _  __| |_ __ ___ | |_/ /_ 
| '_ \| | | |/ _` | '__/ _ \|  __/| |
| | | | |_| | (_| | | | (_) | |   | |
|_| |_|\__, |\__,_|_|  \___/\_|   |_|
        __/ |                        
       |___/
''')

# import modules needed for progress function
import sys
import time


# progress bar
def progress(count, total, status=''):
    bar_len = 28
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('\r[%s] %s%s ...%s' % (bar, percents, '%', status))
    sys.stdout.flush()
    time.sleep(0.10)


# import modules
progress(1, 17, status='importing modules: adafruit')
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
progress(2, 17, status='importing modules: dash')
import dash
import dash_core_components as dcc
from dash.dependencies import Output, Input, Event
import dash_html_components as html
progress(3, 17, status='importing modules: dht22')
import DHT22
progress(4, 17, status='importing modules: pandas')
import pandas as pd
progress(5, 17, status='importing modules: pigpio')
import pigpio as gpio
progress(6, 17, status='importing modules: plotly')
import plotly.graph_objs as go
progress(7, 17, status='importing modules: PyMySQL')
import pymysql as sql
progress(8, 17, status='importing modules: configparser, multiprocessing & warnings')
import configparser as config
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
def sql_db_connect(host, user, passw, db_name, db_table, db_table_2):
    try:
        sql_db_connect.db = sql.connect(host, user, passw)
    except sql.err.OperationalError as e:
        quit(print(e))
    cursor = sql_db_connect.db.cursor()
    cursor.execute('CREATE DATABASE IF NOT EXISTS %s;' % db_name)
    cursor.execute('USE %s;' % db_name)
    cursor.execute('''CREATE TABLE IF NOT EXISTS %s (
        TIME INT NOT NULL, TEMP FLOAT(3, 1) NOT NULL, HUMID FLOAT(3, 1) NOT NULL)''' % db_table)
    cursor.execute('''CREATE TABLE IF NOT EXISTS %s (
        TIME INT NOT NULL, CH0 INT, CH1 INT, CH2 INT, CH3 INT, CH4 INT, CH5 INT, CH6 INT, CH7 INT)''' % db_table_2)


# setup temperature and humidity sensor
def setup_temp_humid(gpio_num):
    pi = gpio.pi()
    if not pi.connected:
        quit(clorox('pi not connected?'))
    setup_temp_humid.dht22 = DHT22.sensor(pi, gpio_num)
    setup_temp_humid.dht22.trigger()
    time.sleep(4)


# read temperature and humidity sensor, store reading in database, read database
def get_temp_humid(db_table, freq):
    while True:
        setup_temp_humid.dht22.trigger()
        time.sleep(4)
        temp = setup_temp_humid.dht22.temperature()
        humid = setup_temp_humid.dht22.humidity()
        cursor = sql_db_connect.db.cursor()
        try:
            cursor.execute('INSERT INTO %s(TIME, TEMP, HUMID) VALUES (%d, %f, %f)' %
                           (db_table, time.time(), temp, humid))
        except sql.err.DataError as e:
            quit(clorox('Check if the DHT22 sensor is connected - ' + str(e)))
        sql_db_connect.db.commit()
        time.sleep(freq)


# setup soil moisture sensor(s)
def setup_soil_moisture(spi_port, spi_device):
    setup_soil_moisture.mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(spi_port, spi_device))


# read soil moisture sensor(s)
def get_soil_moisture(ch, db_table, freq):
    while True:
        for i in ch:
            print(i)
            data = setup_soil_moisture.mcp.read_adc(int(i))
            cursor = sql_db_connect.db.cursor()
            print(data)
            cursor.execute('INSERT INTO %s(TIME, CH%s) VALUES (%f, %i)' %
                           (db_table, i, time.time(), data))
        time.sleep(freq)


# query database
def query(db_select, db_table, limit):
    q = ('SELECT %s FROM %s ORDER BY TIME DESC LIMIT %i' % (db_select, db_table, limit))
    df = pd.read_sql(q, sql_db_connect.db)
    return df


# plot temperature and humidity on a graph using dash
def graph(freq, host, port):
    data_dict = ['Temperature', 'Humidity']
    app = dash.Dash(__name__)
    app.layout = html.Div([
        html.Div([
            html.H1('hydropi')]),
        dcc.Dropdown(id='data-name',
                     options=[{'label': s, 'value': s}
                              for s in data_dict],
                     value=['Temperature'], multi=True),
        html.Div(id='graphs'),
        dcc.Interval(id='update', interval=freq * 1000 + 4000)])

    @app.callback(Output('graphs', 'children'),
                  [Input('data-name', 'value')],
                  events=[Event('update', 'interval')])
    def update_graph(data_names):
        graphs = []
        try:
            returned = query('TIME, TEMP, HUMID', get_conf.conf['DB']['DB_TABLE_TEMP_HUMID'],
                             int(get_conf.conf['GRAPH']['QUERY_LIMIT']))
        except ValueError as e:
            quit(print(e))
        query_data = {'Temperature': (list(returned.TEMP)), 'Humidity': (list(returned.HUMID))}
        if not data_names:
            graphs.append(html.P('Select a graph'))
        else:
            x_date_time = list()
            for i in returned.TIME:
                x_date_time.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i)))
            for name in data_names:
                data = go.Scatter(x=x_date_time, y=query_data[name], mode='lines+markers')
                graphs.append(html.Div(dcc.Graph(
                    id=name, animate=True, figure={'data': [data], 'layout': go.Layout(title=name)})))
        return graphs

    if __name__ == '__main__':
        app.run_server(host=host, port=port)


# monitor soil moisture sensor(s)
def read_soil_moisture(ch, db_table, limit, freq):
    while True:
        data = list()
        for i in ch:
            data.append('CH%s' % i)
        returned = query(', '.join(repr(e) for e in data), db_table, limit)
        print(returned.CH1)
        time.sleep(freq)


# cleanup function
def clorox(e):
    print(e)
    try:
        p_get_temp_humid.terminate()
    except NameError:
        pass
    try:
        p_get_soil_moisture.terminate()
    except NameError:
        pass
    try:
        p_read_soil_moisture.terminate()
    except NameError:
        pass
    try:
        p_graph.terminate()
    except NameError:
        pass
    sql_db_connect.db.close()


# load config
progress(9, 17, status='load config.ini')
get_conf('config.ini')

# connect to database
progress(10, 17, status='connect to mysql and configure required database & tables')
sql_db_connect(get_conf.conf['DB']['HOST'], get_conf.conf['DB']['USER'], get_conf.conf['DB']['PASSW'],
               get_conf.conf['DB']['DB_NAME'], get_conf.conf['DB']['DB_TABLE_TEMP_HUMID'],
               get_conf.conf['DB']['DB_TABLE_SOIL_MOISTURE'])

# setup DHT22 sensor
progress(11, 17, status='setup temperature & humidity sensor')
try:
    setup_temp_humid(int(get_conf.conf['SENSOR']['TEMP_HUMID_GPIO']))
except ValueError as er:
    quit(print('TEMP_HUMID_GPIO must be a number - ' + str(er)))

# setup soil moisture sensor(s)
progress(12, 17, status='setup soil moisture sensor(s)')
setup_soil_moisture(
    int(get_conf.conf['SENSOR']['SOIL_MOISTURE_SPI_PORT']), int(get_conf.conf['SENSOR']['SOIL_MOISTURE_SPI_DEVICE']))

# start processes to run functions with loops
if __name__ == '__main__':
    try:
        # process to read the temperature & humidity sensor
        progress(13, 17, status='starting temperature & humidity reader')
        p_get_temp_humid = Process(target=get_temp_humid,
                                   args=(get_conf.conf['DB']['DB_TABLE_TEMP_HUMID'],
                                         int(get_conf.conf['SENSOR']['TEMP_HUMID_FREQ'])))
        p_get_temp_humid.start()

        # process to read the soil moisture sensor(s)
        progress(14, 17, status='starting soil moisture sensor reader')
        p_get_soil_moisture = Process(target=get_soil_moisture,
                                      args=(get_conf.conf['SENSOR']['SOIL_MOISTURE_SPI_CH'],
                                            get_conf.conf['DB']['DB_TABLE_SOIL_MOISTURE'],
                                            int(get_conf.conf['SENSOR']['SOIL_MOISTURE_FREQ'])))
        p_get_soil_moisture.start()

        # process to read the soil moisture sensor data from the database
        progress(15, 17, status='starting soil moisture sensor monitor')
        p_read_soil_moisture = Process(target=read_soil_moisture,
                                       args=(get_conf.conf['SENSOR']['SOIL_MOISTURE_SPI_CH'],
                                             get_conf.conf['DB']['DB_TABLE_SOIL_MOISTURE'],
                                             int(get_conf.conf['SENSOR']['QUERY_LIMIT']),
                                             int(get_conf.conf['SENSOR']['SOIL_MOISTURE_FREQ_CHECK'])))
        p_read_soil_moisture.start()

        # process to run the graphing agent
        progress(16, 17, status='starting graphing agent')
        p_graph = Process(target=graph,
                          args=(int(get_conf.conf['SENSOR']['TEMP_HUMID_FREQ']), get_conf.conf['GRAPH']['HOST'],
                                int(get_conf.conf['GRAPH']['PORT'])))
        p_graph.start()
        progress(17, 17, status='Done')

    except ValueError as er:
        quit(clorox(str(er)))
