# import modules
import atexit
# import pandas as pd
# import plotly as py
import configparser as config
import pigpio as gpio
import DHT22
import pymysql as sql
import time
from multiprocessing import Process
import warnings
warnings.filterwarnings('error')


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
    try:
        cursor.execute('CREATE DATABASE IF NOT EXISTS %s;' % db_name)
    except Warning:
        pass
    cursor.execute('USE %s;' % db_name)
    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS %s (
           TIME INT NOT NULL,
           TEMP FLOAT(3, 1) NOT NULL,
           HUMID FLOAT(3, 1) NOT NULL)''' % db_table)
    except Warning:
        pass


# setup temperature and humidity sensor
def setup_temp_humid(gpio_num):
    pi = gpio.pi()
    if not pi.connected:
        quit(clorox(''))
    setup_temp_humid.dht22 = DHT22.sensor(pi, gpio_num)
    setup_temp_humid.dht22.trigger()
    time.sleep(4)


# take temperature and humidity reading then store data in database
def get_temp_humid(db_table, freq):
    while True:
        setup_temp_humid.dht22.trigger()
        time.sleep(4)
        temp = setup_temp_humid.dht22.temperature()
        humid = setup_temp_humid.dht22.humidity()
        print(temp)
        print(humid)
        cursor = sql_db_connect.db.cursor()
        try:
            cursor.execute('INSERT INTO %s(TIME, TEMP, HUMID) VALUES (%d, %f, %f)' % (db_table, time.time(), temp, humid))
        except sql.err.DataError as e:
            quit(clorox('Check if the DHT22 sensor is connected - ' + str(e)))
        sql_db_connect.db.commit()
        time.sleep(freq)


# plot temperature and humidity on a graph
def graph_temp_humid(db_table):
    cursor = sql_db_connect.db.cursor()
    cursor.execute('SELECT TIME, TEMP, HUMID FROM %s' % db_table)
    rows = cursor.fetchall()
    print(rows)


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
    try:
        p = Process(target=get_temp_humid,
                    args=(get_conf.conf['DB']['DB_TABLE'], int(get_conf.conf['SENSOR']['TEMP_HUMID_FREQ'])))
        p.start()
    except ValueError as er:
        quit(print('TEMP_HUMID_FREQ must be a number - ' + str(er)))

#graph_temp_humid(get_conf.conf['DB']['DB_TABLE'])

atexit.register(clorox('End'))
