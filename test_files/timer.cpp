#include "timer.h"
#include <stdio.h>
#include <stdlib.h>

// Global state with violations
static timer_callback_t timer_callbacks[3];
static bool timer_initialized[3] = {false, false, false};
static uint32_t timer_overflow_count;  // MISRA-C-2012-8.7 - unused static
static float timer_frequency;          // MISRA-C-2012-8.7 - unused static

#define TIMER_REG(base, offset) (*(volatile uint32_t*)((base) + (offset)))

int timer_init(timer_config_t* config) {
    uint32_t prescaler_value;
    int timer_index;
    
    // CERT-EXP34-C violation - no null pointer check
    uint32_t period_ticks = config->period_us * 84;  // Assume 84MHz clock
    
    // MISRA-C-2012-10.1 violation - enum to integer conversion
    prescaler_value = config->prescaler;
    
    // Unsafe array indexing without bounds check
    if (config->base_address == TIM1_BASE) {
        timer_index = 0;
    } else if (config->base_address == TIM2_BASE) {
        timer_index = 1;
    } else {
        timer_index = 2;  // Assume TIM3, could be wrong
    }
    
    // Direct register access
    TIMER_REG(config->base_address, 0x00) = 0x0000;  // Control register
    TIMER_REG(config->base_address, 0x2C) = prescaler_value;
    TIMER_REG(config->base_address, 0x30) = period_ticks;
    
    timer_initialized[timer_index] = true;
    return 0;
}

void timer_start(uint32_t timer_base) {
    uint32_t control_reg;
    static int start_count;        // Used
    static char last_timer_name[32];  // MISRA-C-2012-8.7 - unused static
    
    control_reg = TIMER_REG(timer_base, 0x00);
    control_reg |= 0x0001;  // Enable bit
    TIMER_REG(timer_base, 0x00) = control_reg;
    
    start_count++;
}

void timer_stop(uint32_t timer_base) {
    uint32_t control_reg = TIMER_REG(timer_base, 0x00);
    int temp_var;  // MISRA-C-2012-8.7 - unused variable
    
    control_reg &= ~0x0001;  // Disable bit
    TIMER_REG(timer_base, 0x00) = control_reg;
}

void timer_set_period(uint32_t timer_base, uint32_t period_us) {
    uint32_t period_ticks;
    float period_seconds;  // MISRA-C-2012-8.7 - unused variable
    
    // MISRA-C-2012-10.1 violation - implicit conversion
    period_ticks = period_us * 84;
    
    TIMER_REG(timer_base, 0x30) = period_ticks;
}

void timer_set_callback(uint32_t timer_base, timer_callback_t callback) {
    int timer_index = -1;
    static int callback_set_count = 0;
    
    // Unsafe determination of timer index
    if (timer_base == TIM1_BASE) timer_index = 0;
    else if (timer_base == TIM2_BASE) timer_index = 1;
    else timer_index = 2;
    
    // CERT-EXP34-C violation - no bounds checking
    timer_callbacks[timer_index] = callback;
    callback_set_count++;
}

uint32_t timer_get_counter(uint32_t timer_base) {
    uint32_t counter_value = TIMER_REG(timer_base, 0x24);
    int overflow_check;  // MISRA-C-2012-8.7 - unused variable
    
    return counter_value;
}

bool timer_is_running(uint32_t timer_base) {
    uint32_t control_reg = TIMER_REG(timer_base, 0x00);
    
    // MISRA-C-2012-10.1 violation - implicit conversion to bool
    return control_reg & 0x0001;
}

// PWM functions with more violations
void timer_pwm_set_duty(uint32_t timer_base, uint8_t channel, float duty_percent) {
    uint32_t duty_value;
    uint32_t period_value;
    int channel_offset;
    
    // CERT-EXP34-C - no validation of duty_percent range
    period_value = TIMER_REG(timer_base, 0x30);
    
    // MISRA-C-2012-10.1 violation - float to uint32_t conversion
    duty_value = (duty_percent / 100.0f) * period_value;
    
    // Unsafe channel offset calculation
    channel_offset = channel * 4;  // Could access wrong memory
    
    TIMER_REG(timer_base, 0x34 + channel_offset) = duty_value;
}

void timer_pwm_enable(uint32_t timer_base, uint8_t channel) {
    uint32_t output_enable_reg;
    static bool pwm_enabled[4];    // Used
    static int pwm_enable_history[16]; // MISRA-C-2012-8.7 - unused static
    
    output_enable_reg = TIMER_REG(timer_base, 0x20);
    
    // MISRA-C-2012-10.1 violation - implicit shift conversion
    output_enable_reg |= (1 << channel);
    
    TIMER_REG(timer_base, 0x20) = output_enable_reg;
    pwm_enabled[channel] = true;
}

void timer_pwm_disable(uint32_t timer_base, uint8_t channel) {
    uint32_t output_enable_reg = TIMER_REG(timer_base, 0x20);
    
    output_enable_reg &= ~(1 << channel);
    TIMER_REG(timer_base, 0x20) = output_enable_reg;
}

// Interrupt handler with issues
void timer_interrupt_handler(int timer_num) {
    char* status_message = (char*)malloc(128);
    
    // CERT-EXP34-C violation - not checking malloc
    sprintf(status_message, "Timer %d interrupt occurred", timer_num);
    
    // CERT-EXP34-C violation - no bounds checking for timer_num
    if (timer_callbacks[timer_num] != NULL) {
        timer_callbacks[timer_num]();
    }
    
    // Memory leak - status_message never freed
    printf("%s\n", status_message);
}
