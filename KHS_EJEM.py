import numpy as np
import time
import logging
import sqlite3
from PyDAQmx import Task
import tkinter as tk
from tkinter import ttk
from threading import Thread

# Configuración de los sensores con canales y rangos específicos
SENSORS = {
    'temperature': {'channel': 'Dev1/ai0', 'range': (-50.0, 150.0)},  # Ejemplo para RTD PT100
    'pressure': {'channel': 'Dev1/ai1', 'range': (0, 100)},  # Ejemplo para Honeywell PX3 Series
    'flow': {'channel': 'Dev1/ai2', 'range': (0, 500)},  # Ejemplo para Siemens SITRANS F M MAG 8000
    'level': {'channel': 'Dev1/ai3', 'range': (0, 10)},  # Ejemplo para VEGAPULS 64
    'position': {'channel': 'Dev1/ai4', 'range': (0, 100)},  # Ejemplo para Macro Sensors PR750
    'force': {'channel': 'Dev1/ai5', 'range': (0, 5000)},  # Ejemplo para HBM C9C
    'vibration': {'channel': 'Dev1/ai6', 'range': (0, 10)},  # Ejemplo para PCB Piezotronics 352C33
    'humidity': {'channel': 'Dev1/ai7', 'range': (0, 100)}  # Ejemplo para Sensirion SHT35
}

# Configuración de logging para registrar eventos y errores
logging.basicConfig(filename='sensor_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Función para configurar la base de datos SQLite
def setup_database():
    conn = sqlite3.connect('sensor_data.db')  # Conectar a la base de datos
    cursor = conn.cursor()  # Crear un cursor para ejecutar comandos
    # Crear una tabla para almacenar los datos de los sensores si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            timestamp TEXT,
            sensor TEXT,
            channel TEXT,
            value REAL
        )
    ''')
    conn.commit()  # Confirmar los cambios en la base de datos
    return conn, cursor  # Devolver la conexión y el cursor

# Función para insertar datos en la base de datos
def insert_data(cursor, conn, timestamp, sensor, channel, value):
    cursor.execute('''
        INSERT INTO sensor_data (timestamp, sensor, channel, value)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, sensor, channel, value))
    conn.commit()  # Confirmar los cambios en la base de datos

# Función para configurar una tarea de adquisición de datos en un canal específico
def configure_task(channel, min_val, max_val):
    task = Task()  # Crear una nueva tarea
    # Configurar el canal de entrada analógica
    task.CreateAIVoltageChan(channel, "", PyDAQmx.DAQmx_Val_Cfg_Default, min_val, max_val, PyDAQmx.DAQmx_Val_Volts, None)
    # Configurar el reloj de adquisición
    task.CfgSampClkTiming("", 1000, PyDAQmx.DAQmx_Val_Rising, PyDAQmx.DAQmx_Val_ContSamps, 1000)
    return task  # Devolver la tarea configurada

# Función para leer datos de la tarea de adquisición
def read_data(task):
    data = np.zeros((1000,), dtype=np.float64)  # Crear un buffer de datos
    # Leer datos del canal
    task.ReadAnalogF64(1000, 10.0, PyDAQmx.DAQmx_Val_GroupByChannel, data, len(data), None, None)
    return np.mean(data)  # Retornar el promedio de los datos leídos

# Función para procesar los datos adquiridos
def process_data(data):
    filtered_data = [x for x in data if 0 < x < 1000]  # Filtrar valores extremos
    return np.mean(filtered_data) if filtered_data else np.nan  # Retornar el promedio filtrado o NaN si no hay datos válidos

# Función para actualizar la interfaz gráfica con los datos de los sensores
def update_gui(sensor_data):
    for sensor, data in sensor_data.items():
        label = sensor_labels[sensor]  # Obtener el widget de la etiqueta del sensor
        label.config(text=f"{sensor}: {data:.2f}")  # Actualizar el texto de la etiqueta

# Función para ejecutar la adquisición de datos en un hilo separado
def acquisition_thread():
    conn, cursor = setup_database()  # Configurar la base de datos
    tasks = {}
    for sensor, config in SENSORS.items():
        try:
            task = configure_task(config['channel'], config['range'][0], config['range'][1])  # Configurar tarea para el sensor
            task.StartTask()  # Iniciar la tarea
            tasks[sensor] = task  # Guardar la tarea en el diccionario
        except Exception as e:
            logging.error(f"Error configurando el sensor {sensor}: {e}")  # Registrar error en la configuración
    
    try:
        while True:
            sensor_data = {}
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # Obtener la hora actual
            for sensor, task in tasks.items():
                try:
                    raw_data = read_data(task)  # Leer datos del sensor
                    processed_data = process_data([raw_data])  # Procesar los datos
                    sensor_data[sensor] = processed_data  # Guardar datos procesados
                    insert_data(cursor, conn, timestamp, sensor, SENSORS[sensor]['channel'], processed_data)  # Insertar datos en la base de datos
                except Exception as e:
                    logging.error(f"Error leyendo datos del sensor {sensor}: {e}")  # Registrar error en la lectura de datos
                    sensor_data[sensor] = np.nan  # Establecer NaN si hay error
            
            update_gui(sensor_data)  # Actualizar la interfaz gráfica
            time.sleep(5)  # Esperar 5 segundos antes de la siguiente lectura

    except KeyboardInterrupt:
        logging.info("Interrupción por teclado, deteniendo el programa.")  # Registrar interrupción por teclado
    finally:
        for sensor, task in tasks.items():
            try:
                task.StopTask()  # Detener la tarea
                task.ClearTask()  # Limpiar la tarea
            except Exception as e:
                logging.error(f"Error deteniendo el sensor {sensor}: {e}")  # Registrar error en la detención de la tarea
        conn.close()  # Cerrar la conexión a la base de datos

# Función para iniciar la adquisición de datos
def start_acquisition():
    acquisition_thread = Thread(target=acquisition_thread, daemon=True)  # Crear un hilo para la adquisición de datos
    acquisition_thread.start()  # Iniciar el hilo

# Configuración de la interfaz gráfica con Tkinter
root = tk.Tk()
root.title("Monitor de Sensores")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Crear etiquetas para mostrar los datos de los sensores en la interfaz gráfica
sensor_labels = {}
for i, sensor in enumerate(SENSORS.keys()):
    label = ttk.Label(frame, text=f"{sensor}: 0.00")
    label.grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
    sensor_labels[sensor] = label

# Crear botón para iniciar la adquisición de datos
start_button = ttk.Button(frame, text="Iniciar Adquisición", command=start_acquisition)
start_button.grid(row=len(SENSORS), column=0, pady=10)

root.mainloop()  # Ejecutar el bucle principal de la interfaz gráfica
