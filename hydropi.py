import configparser as config
import pigpio as gpio
# import DHT22
import pymysql as sql
import time
from multiprocessing import Process


# load config file
def get_conf(file_name):
    get_conf.conf = config.ConfigParser()
    get_conf.conf.read(file_name)


# connect to database and check connectivity
def sql_db_connect(host, user, passw, db_name, error_msg):
    try:
        sql_db_connect.db = sql.connect(host, user, passw, db_name)
    except:
        print(error_msg)


# setup temperature and humidity sensor
def setup_temp_humid(gpio_num, error_msg):
    try:
        pi = gpio.pi()
        dht22 = DHT22.sensor(pi, gpio_num)
        dht22.trigger()
    except:
        print(error_msg)


# take temperature and humidity reading then store data in database
def get_temp_humid(error_msg):
    while True:
        try:
            dht22.trigger()
            temp = dht22.temperature()
            humid = dht22.humidity()
            cursor = sql_db_connect.db.cursor()
            statement = "INSERT INTO TEMP_HUMID(TIME, TEMP, HUMID) VALUES ('%s', %d, %d)" % (time.time(), temp, humid)
            print(statement)
            cursor.execute(statement)
            sql_db_connect.db.commit()
            print('done')
            time.sleep(600)
        except:
            print(error_msg)
            time.sleep(600)


# load config, connect to the database and setup the sensor(s)
get_conf('config.ini')
sql_db_connect(get_conf.conf['DB']['HOST'], get_conf.conf['DB']['USER'], get_conf.conf['DB']['PASSW'],
               get_conf.conf['DB']['DB_NAME'], 'Database Error222')
# setup_temp_humid(get_conf.conf['SENSOR']['TEMP_HUMID_GPIO'], 'Sensor Error')

# start a process to run the get_temp_humid function, this will take temperature and humidity readings every x time
Process(target=get_temp_humid('Sensor Error')).start()

# close database connection
sql_db_connect.db.close()
