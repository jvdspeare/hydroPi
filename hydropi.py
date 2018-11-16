# import modules
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
    except Warning as w:
        print(w)
    cursor.execute('USE %s;' % db_name)
    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS %s (
           TIME INT NOT NULL,
           TEMP FLOAT(3, 1) NOT NULL,
           HUMID FLOAT(3, 1) NOT NULL)''' % db_table)
    except Warning as w:
        print(w)


# setup temperature and humidity sensor
def setup_temp_humid(gpio_num):
    pi = gpio.pi()
    if not pi.connected:
        quit()
    setup_temp_humid.dht22 = DHT22.sensor(pi, gpio_num)
    setup_temp_humid.dht22.trigger()
    time.sleep(4)


# take temperature and humidity reading then store data in database
def get_temp_humid(db_table):
    while True:
        #setup_temp_humid.dht22.trigger()
        #time.sleep(4)
        #temp = setup_temp_humid.dht22.temperature()
        #humid = setup_temp_humid.dht22.humidity()
        temp = -999
        humid = -999
        print(temp)
        print(humid)
        cursor = sql_db_connect.db.cursor()
        try:
            cursor.execute('INSERT INTO %s(TIME, TEMP, HUMID) VALUES (%d, %f, %f)' % (db_table, time.time(), temp, humid))
        except sql.err.DataError as e:
            quit(print('Check if the DHT22 sensor is connected ' + str(e)))
        sql_db_connect.db.commit()
        time.sleep(int(get_conf.conf['SENSOR']['TEMP_HUMID_FREQ']))


# load config, connect to the database and setup the sensor(s)
get_conf('config.ini')
sql_db_connect(get_conf.conf['DB']['HOST'], get_conf.conf['DB']['USER'], get_conf.conf['DB']['PASSW'],
               get_conf.conf['DB']['DB_NAME'], get_conf.conf['DB']['DB_TABLE'])
#setup_temp_humid(int(get_conf.conf['SENSOR']['TEMP_HUMID_GPIO']))

# start a process to run the get_temp_humid function, this will take temperature and humidity readings every x time
Process(target=get_temp_humid(get_conf.conf['DB']['DB_TABLE'])).start()

# close database connection
sql_db_connect.db.close()
