#ifndef TIMER_H
#define TIMER_H

#include <stdint.h>
// Define bool types for compatibility
#ifndef __cplusplus
#define bool _Bool
#define true 1
#define false 0
#endif

// Timer bases
#define TIM1_BASE  0x40010000
#define TIM2_BASE  0x40000000
#define TIM3_BASE  0x40000400

// Timer modes
typedef enum {
    TIMER_MODE_ONESHOT,
    TIMER_MODE_PERIODIC,
    TIMER_MODE_PWM
} timer_mode_t;

// Timer configuration
typedef struct {
    uint32_t base_address;
    timer_mode_t mode;
    uint32_t period_us;
    uint16_t prescaler;
    bool interrupt_enable;
} timer_config_t;

// Callback function type
typedef void (*timer_callback_t)(void);

// Function declarations
int timer_init(timer_config_t* config);
void timer_start(uint32_t timer_base);
void timer_stop(uint32_t timer_base);
void timer_set_period(uint32_t timer_base, uint32_t period_us);
void timer_set_callback(uint32_t timer_base, timer_callback_t callback);
uint32_t timer_get_counter(uint32_t timer_base);
bool timer_is_running(uint32_t timer_base);

// PWM functions
void timer_pwm_set_duty(uint32_t timer_base, uint8_t channel, float duty_percent);
void timer_pwm_enable(uint32_t timer_base, uint8_t channel);
void timer_pwm_disable(uint32_t timer_base, uint8_t channel);

#endif // TIMER_H
