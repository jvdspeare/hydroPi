# hydroPi
Interact with the Environment using Temperature, Humidity, Soil Moisture Sensors & relays to aid in Hydroponics.

## Getting Started

### Hardware
* [Raspberry Pi](https://www.raspberrypi.org/) - ARM single-board Computer (tested using a Raspberry Pi Zero WH)
* [MCP3008](https://www.adafruit.com/product/856) - Microchip to convert Analog to Digital Signal
* [DHT22](https://www.adafruit.com/product/385) - Digital relative Humidity and Temperature Sensor
* [Soil Moisture Sensor](https://www.aliexpress.com/item/Analog-Capacitive-Soil-Moisture-Sensor-V1-2-Corrosion-Resistant-Z09-Drop-ship/32858273308.html) - Analog Capacitive Soil Moisture Sensor
* [Relay](http://www.kumantech.com/kuman-k30-5v-8-channel-relay-shield-module-for-arduino-uno-r3-1280-2560-arm-pic-avr-stm32-raspberry-pi-dsp_p0071.html) - 4 or 8 Channel Relay (any channel size is supported)

#### Where to buy?
I sourced all the components for this project from Amazon.


### Installing
####Install an Operating System on the Raspberry Pi

1. Download Raspbian from [raspberrypi.org](https://www.raspberrypi.org/downloads/raspbian/) - 
the lite distribution is recommended.
2. Install Raspbian on the SD card - you can use a tool like [Rufus](https://rufus.ie/en_IE.html) on Windows or [Etcher](https://www.balena.io/etcher/) on Mac OS to create the image and write it to the SD Card.
3. Boot and SSH to the Raspberry Pi - If you are on Windows [PuTTY](https://www.putty.org/) is an SSH Client which you can use. On Mac OS SSH using the terminal
    ```
    ssh pi@192.168.0.1
    ```

####Configure the Raspberry Pi

Once you have an open SSH session with the Raspberry Pi we can start getting a basic configuration in place
1. Make sure your Raspberry Pi is up-to-date
    ```
    sudo apt-get update && sudo apt-get upgrade
    ```
2. Install pip for Python 3
    ```
    sudo apt-get install python3-pip
    ```
3. Enable SPI
    ```
    sudo raspi-config
    ```
Select option 5 - Interfacing Options - then select SPI and confirm you wish to enable it.

## Built With
* [Adafruit](https://github.com/adafruit) - libraries for interfacing with the MCP3008 & SPI
* [dash](https://github.com/plotly/dash) - Analytical Web Apps for Python. No JavaScript Required
* [pandas](https://github.com/pandas-dev/pandas) - Flexible and powerful data analysis / manipulation library for Python
* [pigpio](http://abyz.me.uk/rpi/pigpio/) - Libraries for interfacing with the GPIO pins and DHT22 sensor
* [PyMySQL](https://github.com/PyMySQL/PyMySQL) - Pure Python MySQL Client

## Authors
* jvdspeare

## License
This project is licensed under the MIT License - see the LICENSE.md file for details