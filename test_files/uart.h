#ifndef UART_H
#define UART_H

#include <stdint.h>
// Define bool types for compatibility
#ifndef __cplusplus
#define bool _Bool
#define true 1
#define false 0
#endif

// UART configuration
#define UART1_BASE 0x40013800
#define UART2_BASE 0x40004400
#define UART3_BASE 0x40004800

// Baud rates
typedef enum {
    BAUD_9600 = 9600,
    BAUD_19200 = 19200,
    BAUD_38400 = 38400,
    BAUD_115200 = 115200
} uart_baud_t;

// UART configuration structure
typedef struct {
    uint32_t base_address;
    uart_baud_t baud_rate;
    uint8_t data_bits;
    uint8_t stop_bits;
    bool parity_enable;
} uart_config_t;

// Buffer structure
typedef struct {
    char* data;
    uint16_t size;
    uint16_t head;
    uint16_t tail;
} uart_buffer_t;

// Function declarations
int uart_init(uart_config_t* config);
int uart_send_byte(uint32_t uart_base, uint8_t data);
int uart_send_string(uint32_t uart_base, const char* str);
int uart_receive_byte(uint32_t uart_base);
bool uart_data_available(uint32_t uart_base);

// Buffer management
uart_buffer_t* uart_create_buffer(uint16_t size);
void uart_destroy_buffer(uart_buffer_t* buffer);
int uart_buffer_write(uart_buffer_t* buffer, char data);
int uart_buffer_read(uart_buffer_t* buffer);

#endif // UART_H
