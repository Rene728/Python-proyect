iimport numpy as np
import time
import logging
import sqlite3
from threading import Thread
from queue import Queue
from PyDAQmx import Task, DAQmx_Val_Cfg_Default, DAQmx_Val_Volts, DAQmx_Val_Rising, DAQmx_Val_ContSamps
from pymodbus.client.sync import ModbusTcpClient
import socket
from typing import Dict, Tuple, Any

# Configuración de logging para registrar eventos y errores
logging.basicConfig(
    filename='sensor_log.txt',  # Archivo de registro
    level=logging.INFO,         # Nivel de logging: INFO
    format='%(asctime)s - %(levelname)s - %(message)s'  # Formato del mensaje de logging
)

# Configuración de los sensores con canales y rangos específicos
SENSORS = {
    'temperature': {'channel': 'Dev1/ai0', 'range': (-50.0, 150.0)},
    'pressure': {'channel': 'Dev1/ai1', 'range': (0, 100)},
    'flow': {'channel': 'Dev1/ai2', 'range': (0, 500)},
    'level': {'channel': 'Dev1/ai3', 'range': (0, 10)},
    'position': {'channel': 'Dev1/ai4', 'range': (0, 100)},
    'force': {'channel': 'Dev1/ai5', 'range': (0, 5000)},
    'vibration': {'channel': 'Dev1/ai6', 'range': (0, 10)},
    'humidity': {'channel': 'Dev1/ai7', 'range': (0, 100)}
}

# Configuración de la base de datos SQLite
def setup_database() -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    """
    Configura la base de datos SQLite para almacenar los datos de los sensores.
    Crea la tabla si no existe.
    """
    conn = sqlite3.connect('sensor_data.db')  # Conectar o crear base de datos
    cursor = conn.cursor()  # Crear un cursor para ejecutar comandos SQL
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            timestamp TEXT,  # Fecha y hora de la lectura
            sensor TEXT,     # Nombre del sensor
            channel TEXT,    # Canal del sensor
            value REAL        # Valor leído del sensor
        )
    ''')
    conn.commit()  # Guardar cambios en la base de datos
    return conn, cursor

# Inserción de datos en la base de datos
def insert_data(cursor: sqlite3.Cursor, conn: sqlite3.Connection, timestamp: str, sensor: str, channel: str, value: float):
    """
    Inserta una entrada de datos en la base de datos.
    """
    try:
        cursor.execute('''
            INSERT INTO sensor_data (timestamp, sensor, channel, value)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, sensor, channel, value))
        conn.commit()  # Guardar cambios en la base de datos
    except sqlite3.Error as e:
        logging.error(f"Error al insertar datos en la base de datos: {e}")  # Registrar error en el archivo de log

# Configuración de la tarea de adquisición de datos
def configure_task(channel: str, min_val: float, max_val: float) -> Task:
    """
    Configura una tarea de adquisición de datos para un canal específico.
    """
    task = Task()  # Crear una nueva tarea
    task.CreateAIVoltageChan(channel, "", DAQmx_Val_Cfg_Default, min_val, max_val, DAQmx_Val_Volts, None)
    task.CfgSampClkTiming("", 1000, DAQmx_Val_Rising, DAQmx_Val_ContSamps, 1000)  # Configurar el reloj de muestreo
    return task

# Lectura de datos desde el canal configurado
def read_data(task: Task) -> np.ndarray:
    """
    Lee datos del canal de adquisición.
    """
    data = np.zeros((1000,), dtype=np.float64)  # Inicializar un array para los datos
    try:
        task.ReadAnalogF64(1000, 10.0, DAQmx_Val_GroupByChannel, data, len(data), None, None)
    except Exception as e:
        logging.error(f"Error al leer datos del sensor: {e}")  # Registrar error en el archivo de log
    return data

# Procesamiento de datos para eliminar valores atípicos y calcular el promedio
def process_data(data: np.ndarray) -> float:
    """
    Procesa los datos leídos para filtrar valores atípicos y calcular el promedio.
    """
    try:
        filtered_data = [x for x in data if 0 < x < 1000]  # Filtrar valores atípicos
        return np.mean(filtered_data) if filtered_data else np.nan  # Calcular el promedio
    except Exception as e:
        logging.error(f"Error al procesar datos: {e}")  # Registrar error en el archivo de log
        return np.nan

# Adquisición de datos de todos los sensores
def acquire_sensor_data(queue: Queue):
    """
    Adquiere y procesa datos de todos los sensores configurados.
    """
    conn, cursor = setup_database()  # Configurar la base de datos
    tasks = {}  # Diccionario para almacenar las tareas de adquisición de datos
    sensor_data = {}  # Diccionario para almacenar los datos leídos
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # Obtener la fecha y hora actual

    # Configuración de tareas para todos los sensores
    for sensor, config in SENSORS.items():
        try:
            task = configure_task(config['channel'], config['range'][0], config['range'][1])
            task.StartTask()  # Iniciar la tarea de adquisición de datos
            tasks[sensor] = task  # Almacenar la tarea en el diccionario
        except Exception as e:
            logging.error(f"Error configurando el sensor {sensor}: {e}")  # Registrar error en el archivo de log

    # Lectura y procesamiento de datos para todos los sensores
    for sensor, task in tasks.items():
        try:
            raw_data = read_data(task)  # Leer datos del sensor
            processed_data = process_data(raw_data)  # Procesar los datos leídos
            sensor_data[sensor] = processed_data  # Almacenar los datos procesados
            insert_data(cursor, conn, timestamp, sensor, SENSORS[sensor]['channel'], processed_data)  # Insertar datos en la base de datos
        except Exception as e:
            logging.error(f"Error procesando datos del sensor {sensor}: {e}")  # Registrar error en el archivo de log
        finally:
            task.StopTask()  # Detener la tarea
            task.ClearTask()  # Limpiar la tarea

    conn.close()  # Cerrar la conexión a la base de datos
    queue.put(sensor_data)  # Enviar los datos al hilo principal a través de una cola

# Enviar datos a LabVIEW mediante un archivo compartido
def send_to_labview(sensor_data: Dict[str, float]):
    """
    Escribe los datos de los sensores en un archivo de texto para que LabVIEW pueda leerlos.
    """
    try:
        with open('sensor_data.txt', 'w') as file:
            for sensor, value in sensor_data.items():
                file.write(f"{sensor}: {value}\n")
    except Exception as e:
        logging.error(f"Error al escribir datos para LabVIEW: {e}")  # Registrar error en el archivo de log

# Comunicación con el PLC utilizando Modbus
def communicate_with_plc(sensor_data: Dict[str, float]):
    """
    Envía datos de sensores al PLC utilizando el protocolo Modbus TCP.
    """
    client = ModbusTcpClient('192.168.1.100')  # Dirección IP del PLC
    if not client.connect():
        logging.error("No se pudo conectar al PLC")
        return
    
    try:
        address = 0  # Dirección de inicio para los registros
        for sensor, value in sensor_data.items():
            # Convertir el valor a entero para escribir en el PLC
            int_value = int(value * 100)  # Ejemplo: escalado para el PLC
            client.write_register(address, int_value)  # Escribir valor en el PLC
            address += 1  # Incrementar la dirección para el próximo valor
    except Exception as e:
        logging.error(f"Error al comunicar con el PLC: {e}")  # Registrar error en el archivo de log
    finally:
        client.close()  # Cerrar la conexión al PLC

# Función principal para ejecutar la adquisición de datos, enviar a LabVIEW y PLC
def main():
    queue = Queue()  # Cola para comunicación entre hilos
    acquire_thread = Thread(target=acquire_sensor_data, args=(queue,))  # Hilo para adquisición de datos
    acquire_thread.start()  # Iniciar el hilo de adquisición
    
    while acquire_thread.is_alive():
        time.sleep(10)  # Esperar mientras se adquieren los datos
        
        # Procesar los datos adquiridos
        if not queue.empty():
            sensor_data = queue.get()  # Obtener los datos de la cola
            send_to_labview(sensor_data)  # Enviar datos a LabVIEW
            communicate_with_plc(sensor_data)  # Enviar datos al PLC
    
    acquire_thread.join()  # Esperar a que termine el hilo de adquisición

if __name__ == "__main__":
    main()

