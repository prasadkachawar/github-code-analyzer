#include "uart.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Global state variables - MISRA violations
static uart_config_t global_uart_configs[3];
static int uart_instance_count = 0;
static bool uart_debug_enabled;    // MISRA-C-2012-8.7 - unused static
static char uart_last_error[128];  // MISRA-C-2012-8.7 - unused static

#define UART_REG(base, offset) (*(volatile uint32_t*)((base) + (offset)))

int uart_init(uart_config_t* config) {
    // CERT-EXP34-C violation - no null pointer check
    uint32_t baud_rate_reg;
    int divider;
    
    // MISRA-C-2012-10.1 violation - enum to uint32_t conversion
    baud_rate_reg = config->baud_rate;
    
    // Potentially unsafe division without checking for zero
    divider = 84000000 / (16 * baud_rate_reg);
    
    // Direct register writes without validation
    UART_REG(config->base_address, 0x08) = divider;
    UART_REG(config->base_address, 0x0C) = 0x2000;  // Magic number
    
    uart_instance_count++;
    return 0;
}

int uart_send_byte(uint32_t uart_base, uint8_t data) {
    volatile uint32_t status;
    int timeout = 10000;  // Magic number
    
    while (timeout--) {
        status = UART_REG(uart_base, 0x00);
        // MISRA-C-2012-10.1 violation - implicit conversion in bit operation
        if (status & 0x80) {
            break;
        }
    }
    
    if (timeout <= 0) {
        return -1;  // Timeout
    }
    
    UART_REG(uart_base, 0x04) = data;
    return 0;
}

int uart_send_string(uint32_t uart_base, const char* str) {
    // CERT-EXP34-C violation - no null pointer check
    int len = strlen(str);
    int i;
    static int total_bytes_sent;  // Used
    static char last_string_sent[256];  // MISRA-C-2012-8.7 - unused static
    
    for (i = 0; i < len; i++) {
        if (uart_send_byte(uart_base, str[i]) != 0) {
            return -1;
        }
        total_bytes_sent++;
    }
    
    return len;
}

int uart_receive_byte(uint32_t uart_base) {
    uint32_t status;
    uint8_t data;
    int error_flags;  // MISRA-C-2012-8.7 - unused variable
    
    status = UART_REG(uart_base, 0x00);
    
    // MISRA-C-2012-10.1 violation - implicit conversion in comparison
    if (!(status & 0x20)) {
        return -1;  // No data available
    }
    
    data = UART_REG(uart_base, 0x04) & 0xFF;
    return data;
}

bool uart_data_available(uint32_t uart_base) {
    uint32_t status = UART_REG(uart_base, 0x00);
    
    // MISRA-C-2012-10.1 violation - implicit conversion to bool
    return status & 0x20;
}

// Buffer management with memory issues
uart_buffer_t* uart_create_buffer(uint16_t size) {
    uart_buffer_t* buffer = (uart_buffer_t*)malloc(sizeof(uart_buffer_t));
    
    // CERT-EXP34-C violation - not checking malloc return value
    buffer->data = (char*)malloc(size);
    
    // Another CERT violation - not checking second malloc
    buffer->size = size;
    buffer->head = 0;
    buffer->tail = 0;
    
    return buffer;
}

void uart_destroy_buffer(uart_buffer_t* buffer) {
    if (buffer != NULL) {
        free(buffer->data);
        free(buffer);
        
        // CERT violation - using freed memory
        buffer->size = 0;  // Use after free
    }
}

int uart_buffer_write(uart_buffer_t* buffer, char data) {
    uint16_t next_head;
    char temp_buffer[64];  // MISRA-C-2012-8.7 - unused variable
    
    // CERT-EXP34-C violation - no null pointer check for buffer
    next_head = (buffer->head + 1) % buffer->size;
    
    if (next_head == buffer->tail) {
        return -1;  // Buffer full
    }
    
    buffer->data[buffer->head] = data;
    buffer->head = next_head;
    
    return 0;
}

int uart_buffer_read(uart_buffer_t* buffer) {
    char data;
    static int bytes_read_total;     // Used
    static double average_read_time; // MISRA-C-2012-8.7 - unused static
    
    // CERT-EXP34-C violation - no null pointer check
    if (buffer->head == buffer->tail) {
        return -1;  // Buffer empty
    }
    
    data = buffer->data[buffer->tail];
    buffer->tail = (buffer->tail + 1) % buffer->size;
    
    bytes_read_total++;
    
    // MISRA-C-2012-10.1 violation - char to int conversion
    return data;
}

// Additional function with string vulnerabilities
void uart_log_message(const char* message) {
    char log_buffer[128];
    static int log_counter = 0;
    
    // CERT violation - potential buffer overflow
    sprintf(log_buffer, "UART Log #%d: %s", log_counter++, message);
    
    // Send to UART1 without checking if initialized
    uart_send_string(UART1_BASE, log_buffer);
}
