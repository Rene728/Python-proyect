// Control subystem
#include <xc.h>
#include <stdint.h>

// Configuración de los bits de configuración
#pragma config FOSC = INTOSCIO_EC // Oscilador interno
#pragma config WDT = OFF          // Watchdog Timer apagado
#pragma config LVP = OFF          // Programación en bajo voltaje apagada

#define _XTAL_FREQ 8000000 // Frecuencia del oscilador interno (8 MHz)

// Direcciones I2C de los subsistemas
#define EXTRACTION_SUBSYSTEM_ADDRESS 0x51
#define TRACTION_SUBSYSTEM_ADDRESS 0x52
#define MIXING_SUBSYSTEM_ADDRESS 0x53

void I2C_Master_Init(void) {
    SSPCON1 = 0b00101000; // Habilitar I2C master mode
    SSPCON2 = 0;
    SSPADD = (_XTAL_FREQ / (4 * 100000)) - 1; // Configuración de la velocidad del reloj I2C
    SSPSTAT = 0;
}

void I2C_Master_Wait(void) {
    while ((SSPCON2 & 0x1F) || (SSPSTAT & 0x04));
}

void I2C_Master_Start(void) {
    I2C_Master_Wait();
    SEN = 1; // Iniciar condición start
}

void I2C_Master_Stop(void) {
    I2C_Master_Wait();
    PEN = 1; // Iniciar condición stop
}

void I2C_Master_Write(unsigned char data) {
    I2C_Master_Wait();
    SSPBUF = data; // Escribir datos al buffer
}

unsigned char I2C_Master_Read(unsigned char ack) {
    unsigned char data;
    I2C_Master_Wait();
    RCEN = 1;
    I2C_Master_Wait();
    data = SSPBUF;
    I2C_Master_Wait();
    ACKDT = (ack) ? 0 : 1; // Acknowledgment bit
    ACKEN = 1; // Enviar bit de acknowledgment
    return data;
}

void send_signal_to_extraction_subsystem(void) {
    I2C_Master_Start();
    I2C_Master_Write(EXTRACTION_SUBSYSTEM_ADDRESS << 1);
    I2C_Master_Write(0x01); // Señal para iniciar extracción
    I2C_Master_Stop();
}

void main(void) {
    OSCCON = 0x70; // Configurar oscilador interno a 8 MHz
    I2C_Master_Init(); // Inicializar I2C master

    while (1) {
        send_signal_to_extraction_subsystem();
        __delay_ms(1000);
    }
}
