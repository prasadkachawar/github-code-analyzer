#include "gpio.h"
#include <stdio.h>
#include <stdint.h>

// Static variables with issues
static uint32_t gpio_initialized = 0;
static gpio_config_t last_config;  // MISRA-C-2012-8.7 - unused static
static int debug_counter;          // MISRA-C-2012-8.7 - unused static

// Volatile register access (unsafe)
#define GPIO_REG(base, offset) (*(volatile uint32_t*)((base) + (offset)))

void gpio_init(gpio_config_t* config) {
    // CERT-EXP34-C violation - no null pointer check
    uint32_t port_addr = config->port_base;
    
    // MISRA-C-2012-10.1 violation - implicit conversion
    uint8_t pin_mask = 1 << config->pin_number;  // Could overflow
    
    // Direct register manipulation without bounds checking
    GPIO_REG(port_addr, 0x00) = pin_mask;
    
    gpio_initialized = 1;
}

void gpio_set_pin(uint32_t port, uint8_t pin, gpio_state_t state) {
    int pin_value;  // MISRA-C-2012-8.7 - could be static or removed
    
    // MISRA-C-2012-10.1 violation - enum to int conversion
    pin_value = state;
    
    if (pin > 16) {  // Magic number - should be #define
        printf("Invalid pin number: %d\n", pin);
        return;
    }
    
    // Unsafe bit manipulation
    if (pin_value) {
        GPIO_REG(port, 0x14) |= (1 << pin);
    } else {
        GPIO_REG(port, 0x18) |= (1 << pin);
    }
}

gpio_state_t gpio_read_pin(uint32_t port, uint8_t pin) {
    uint32_t reg_value;
    int result;  // MISRA-C-2012-8.7 - unused local variable
    
    reg_value = GPIO_REG(port, 0x10);
    
    // MISRA-C-2012-10.1 violation - unsigned to signed conversion
    if (reg_value & (1 << pin)) {
        return GPIO_HIGH;
    }
    
    return GPIO_LOW;
}

void gpio_toggle_pin(uint32_t port, uint8_t pin) {
    gpio_state_t current_state = gpio_read_pin(port, pin);
    static int toggle_count;  // Used
    static float last_toggle_time;  // MISRA-C-2012-8.7 - unused static
    
    toggle_count++;
    
    if (current_state == GPIO_HIGH) {
        gpio_set_pin(port, pin, GPIO_LOW);
    } else {
        gpio_set_pin(port, pin, GPIO_HIGH);
    }
}

// Functions with memory issues
void gpio_interrupt_enable(uint32_t port, uint8_t pin) {
    uint32_t* interrupt_reg = (uint32_t*)malloc(sizeof(uint32_t));
    
    // CERT-EXP34-C violation - not checking malloc return
    *interrupt_reg = GPIO_REG(port, 0x0C);
    *interrupt_reg |= (1 << pin);
    GPIO_REG(port, 0x0C) = *interrupt_reg;
    
    // Memory leak - never freed
}

void gpio_interrupt_disable(uint32_t port, uint8_t pin) {
    char local_buffer[64];
    
    sprintf(local_buffer, "Disabling interrupt for pin %d", pin);
    printf("%s\n", local_buffer);
    
    GPIO_REG(port, 0x0C) &= ~(1 << pin);
    
    // CERT violation - returning address of local variable implicitly
}
