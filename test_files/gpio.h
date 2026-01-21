#ifndef GPIO_H
#define GPIO_H

#include <stdint.h>

// GPIO port definitions
#define GPIO_PORT_A  0x40020000
#define GPIO_PORT_B  0x40020400
#define GPIO_PORT_C  0x40020800

// GPIO pin states
typedef enum {
    GPIO_LOW = 0,
    GPIO_HIGH = 1
} gpio_state_t;

// GPIO configuration structure
typedef struct {
    uint32_t port_base;
    uint8_t pin_number;
    uint8_t direction;  // 0 = input, 1 = output
} gpio_config_t;

// Function declarations
void gpio_init(gpio_config_t* config);
void gpio_set_pin(uint32_t port, uint8_t pin, gpio_state_t state);
gpio_state_t gpio_read_pin(uint32_t port, uint8_t pin);
void gpio_toggle_pin(uint32_t port, uint8_t pin);

// Interrupt handlers
void gpio_interrupt_enable(uint32_t port, uint8_t pin);
void gpio_interrupt_disable(uint32_t port, uint8_t pin);

#endif // GPIO_H
