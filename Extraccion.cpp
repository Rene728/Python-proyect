// Subsistema de extraccion
#include <xc.h>
#include <stdint.h>

// Configuración de los bits de configuración
#pragma config FOSC = INTOSCIO_EC // Oscilador interno
#pragma config WDT = OFF          // Watchdog Timer apagado
#pragma config LVP = OFF          // Programación en bajo voltaje apagada

#define _XTAL_FREQ 8000000 // Frecuencia del oscilador interno (8 MHz)

// Dirección I2C del subsistema de extracción
#define EXTRACTION_SUBSYSTEM_ADDRESS 0x51

void I2C_Slave_Init(unsigned char address) {
    SSPADD = address; // Configurar dirección del esclavo
    SSPCON1 = 0b00110110; // Habilitar I2C esclavo mode
    SSPCON2 = 0;
    SSPSTAT = 0;
    SSPCON1bits.SSPEN = 1; // Habilitar el puerto MSSP
    PIE1bits.SSPIE = 1; // Habilitar interrupciones I2C
    INTCONbits.PEIE = 1; // Habilitar interrupciones periféricas
    INTCONbits.GIE = 1; // Habilitar interrupciones globales
}

void __interrupt() ISR(void) {
    if (PIR1bits.SSPIF) {
        PIR1bits.SSPIF = 0; // Limpiar bandera de interrupción
        if (!SSPSTATbits.D_nA && !SSPSTATbits.R_nW) {
            // Dirección + escritura recibida
            unsigned char data = SSPBUF; // Leer el buffer para limpiar la bandera BF
            while (!SSPSTATbits.BF); // Esperar hasta que se reciba el dato
            data = SSPBUF; // Leer dato recibido
            if (data == 0x01) {
                // Iniciar extracción
                // Código para activar el efector final
                // ...
                // Enviar señal de finalización al subsistema de control
            }
        }
    }
}

void main(void) {
    OSCCON = 0x70; // Configurar oscilador interno a 8 MHz
    I2C_Slave_Init(EXTRACTION_SUBSYSTEM_ADDRESS); // Inicializar I2C esclavo

    while (1) {
        // Loop principal del esclavo
    }
}
