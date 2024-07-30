
from machine import Pin, I2C, SPI
import os
import sdcard
import time

# Configuración del SPI para la tarjeta SD
spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
cs = Pin(15, Pin.OUT)

# Inicialización de la tarjeta SD
sd = sdcard.SDCard(spi, cs)
os.mount(sd, '/sd')

# Configuración de la comunicación I2C
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
CONTROL_SUBSYSTEM_ADDRESS = 0x50

def read_sd_file(file_name):
    with open('/sd/' + file_name, 'r') as file:
        data = file.readlines()
    return data

def send_trajectory_data(data):
    for line in data:
        # Convertir la línea a bytes y enviar por I2C
        i2c.writeto(CONTROL_SUBSYSTEM_ADDRESS, bytes(line.strip(), 'utf-8'))
        time.sleep(0.1)

# Ejemplo de lectura de un archivo de trayectoria y envío de datos
trajectory_data = read_sd_file('trajectory.txt')
send_trajectory_data(trajectory_data)

# Desmontar la tarjeta SD al finalizar
os.umount('/sd')
