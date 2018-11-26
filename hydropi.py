# import modules
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, Event
import pandas as pd
import plotly.graph_objs as go
import configparser as config
import pigpio as gpio
import DHT22
import MCP3008
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
def setup_soil_moisture():
    SPI_PORT = 0
    SPI_DEVICE = 0
    setup_soil_moisture.mcp = MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))


# read soil moisture sensor(s)
def get_soil_moisture():
    data = setup_soil_moisture.mcp.read_adc(1)
    print(data)
    time.sleep(3)

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
            returned = query('TIME, TEMP, HUMID', get_conf.conf['DB']['DB_TABLE'],
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


# cleanup function
def clorox(e):
    print(e)
    try:
        p_get_temp_humid.terminate()
    except NameError:
        pass
    try:
        p_graph.terminate()
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

# setup soil moisture sensor(s)
setup_soil_moisture()

# start a process to run the get_temp_humid function
if __name__ == '__main__':
    try:
        p_get_temp_humid = Process(target=get_temp_humid,
                                   args=(get_conf.conf['DB']['DB_TABLE'],
                                         int(get_conf.conf['SENSOR']['TEMP_HUMID_FREQ'])))
        p_get_temp_humid.start()
        p_get_soil_moisture = Process(target=get_soil_moisture)
        p_get_soil_moisture.start()
        p_graph = Process(target=graph,
                          args=(int(get_conf.conf['SENSOR']['TEMP_HUMID_FREQ']), get_conf.conf['GRAPH']['HOST'],
                                int(get_conf.conf['GRAPH']['PORT'])))
        p_graph.start()
    except ValueError as er:
        quit(clorox('TEMP_HUMID_FREQ must be a number - ' + str(er)))
