#include "gpio.h"
#include "uart.h"
#include "timer.h"
#include "adc.h"
#include "sensor.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// System-wide global variables with issues
static bool system_initialized = false;
static uint32_t system_uptime_ms = 0;
static char system_version[32] = "v1.0.0";
static int error_count;                    // MISRA-C-2012-8.7 - unused static
static float system_temperature;           // MISRA-C-2012-8.7 - unused static
static char last_error_message[256];      // MISRA-C-2012-8.7 - unused static

// System initialization with cross-module dependencies
int system_init(void) {
    gpio_config_t gpio_cfg;
    uart_config_t uart_cfg;
    timer_config_t timer_cfg;
    adc_config_t adc_cfg;
    
    // CERT-EXP34-C violations - using uninitialized struct members
    gpio_cfg.port_base = GPIO_PORT_A;
    gpio_cfg.pin_number = 5;
    // Missing: gpio_cfg.direction initialization
    
    uart_cfg.base_address = UART1_BASE;
    uart_cfg.baud_rate = BAUD_115200;
    // Missing: uart_cfg.data_bits, stop_bits, parity_enable
    
    // MISRA-C-2012-10.1 violation - implicit conversions
    timer_cfg.base_address = TIM1_BASE;
    timer_cfg.mode = TIMER_MODE_PERIODIC;
    timer_cfg.period_us = 1000;  // 1ms
    
    adc_cfg.base_address = ADC1_BASE;
    adc_cfg.resolution = ADC_RES_12BIT;
    
    // Initialize all subsystems without error checking
    gpio_init(&gpio_cfg);
    uart_init(&uart_cfg);
    timer_init(&timer_cfg);
    adc_init(&adc_cfg);
    
    system_initialized = true;
    return 0;
}

// System main loop with multiple violations
void system_main_loop(void) {
    SensorData* sensor_data;
    uint16_t adc_values[4];
    char status_buffer[128];
    static int loop_count = 0;
    static char loop_debug_info[512];  // MISRA-C-2012-8.7 - unused static
    
    while (system_initialized) {
        loop_count++;
        
        // Read sensor data with potential null pointer issues
        sensor_data = read_sensor_data(1);
        
        // CERT-EXP34-C violation - no null pointer check
        if (sensor_data->temperature > 85.0f) {
            // CERT violation - potential buffer overflow
            sprintf(status_buffer, "OVERHEAT: Temperature is %f degrees", 
                   sensor_data->temperature);
            uart_send_string(UART1_BASE, status_buffer);
        }
        
        // Read ADC values without error handling
        adc_read_multiple(ADC1_BASE, adc_values, 4);
        
        // MISRA-C-2012-10.1 violation - array indexing with signed int
        for (int i = 0; i < 4; i++) {
            float voltage = adc_to_voltage(adc_values[i], 3.3f);
            
            // Unsafe string operations
            char adc_msg[64];
            sprintf(adc_msg, "ADC%d: %.2fV\n", i, voltage);
            uart_send_string(UART1_BASE, adc_msg);
        }
        
        // Update system uptime without overflow protection
        system_uptime_ms++;
        
        // Memory cleanup issues
        sensor_cleanup(sensor_data);
        
        // Artificial delay
        for (volatile int delay = 0; delay < 100000; delay++);
    }
}

// Error handling with string vulnerabilities
void system_handle_error(int error_code, const char* error_msg) {
    char full_error_msg[256];
    static int total_errors = 0;
    static char error_history[10][128];  // MISRA-C-2012-8.7 - unused static
    
    total_errors++;
    
    // CERT violation - potential buffer overflow with sprintf
    sprintf(full_error_msg, "[ERROR %d] System Error #%d: %s (uptime: %ums)", 
            error_code, total_errors, error_msg, system_uptime_ms);
    
    // Send error via UART without checking if initialized
    uart_send_string(UART1_BASE, full_error_msg);
    
    // Toggle error LED
    gpio_toggle_pin(GPIO_PORT_C, 13);
}

// Configuration loading with file operations (simulated)
int system_load_config(const char* filename) {
    FILE* config_file;
    char line_buffer[256];
    char* config_data = (char*)malloc(1024);
    int bytes_read = 0;
    static char config_backup[1024];  // MISRA-C-2012-8.7 - unused static
    
    // CERT-EXP34-C violation - not checking malloc return
    // CERT-EXP34-C violation - no null pointer check for filename
    
    config_file = fopen(filename, "r");
    if (config_file == NULL) {
        system_handle_error(100, "Cannot open config file");
        return -1;
    }
    
    // Unsafe file reading with potential buffer overflow
    while (fgets(line_buffer, sizeof(line_buffer), config_file) != NULL) {
        // CERT violation - no bounds checking for config_data
        strcat(config_data, line_buffer);
        bytes_read += strlen(line_buffer);
    }
    
    fclose(config_file);
    
    // Process configuration (simplified)
    if (strstr(config_data, "debug=true") != NULL) {
        printf("Debug mode enabled\n");
    }
    
    // Memory leak - config_data never freed
    return 0;
}

// System statistics with type conversion issues
void system_print_stats(void) {
    uint32_t uptime_seconds;
    float uptime_hours;
    int memory_usage;  // MISRA-C-2012-8.7 - unused variable
    
    // MISRA-C-2012-10.1 violation - implicit conversion
    uptime_seconds = system_uptime_ms / 1000;
    
    // MISRA-C-2012-10.1 violation - uint32_t to float conversion
    uptime_hours = uptime_seconds / 3600.0f;
    
    printf("=== System Statistics ===\n");
    printf("Uptime: %u seconds (%.2f hours)\n", uptime_seconds, uptime_hours);
    printf("System Version: %s\n", system_version);
    printf("Initialized: %s\n", system_initialized ? "YES" : "NO");
}

// Watchdog simulation with timing issues
void system_watchdog_feed(void) {
    static uint32_t last_feed_time = 0;
    static uint32_t feed_interval = 1000;  // 1 second
    static int missed_feeds = 0;           // Used
    static float feed_efficiency;          // MISRA-C-2012-8.7 - unused static
    
    uint32_t current_time = system_uptime_ms;
    
    // MISRA-C-2012-10.1 violation - unsigned arithmetic that could underflow
    if ((current_time - last_feed_time) > feed_interval) {
        // Feed watchdog (hardware register write simulation)
        *((volatile uint32_t*)0x40002C00) = 0xAAAA;
        last_feed_time = current_time;
    } else {
        missed_feeds++;
        if (missed_feeds > 5) {
            system_handle_error(200, "Watchdog feed missed multiple times");
        }
    }
}

// System shutdown with resource cleanup issues
void system_shutdown(void) {
    char* shutdown_msg = (char*)malloc(128);
    
    // CERT-EXP34-C violation - not checking malloc
    sprintf(shutdown_msg, "System shutting down after %u ms uptime", 
            system_uptime_ms);
    
    uart_send_string(UART1_BASE, shutdown_msg);
    
    // Disable all peripherals
    timer_stop(TIM1_BASE);
    adc_stop_conversion(ADC1_BASE);
    
    // Set shutdown flag
    system_initialized = false;
    
    // Memory leak - shutdown_msg never freed
    // Missing: proper resource deallocation for other modules
}
