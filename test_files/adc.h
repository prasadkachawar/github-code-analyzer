#ifndef ADC_H
#define ADC_H

#include <stdint.h>
// Define bool types for compatibility
#ifndef __cplusplus
#define bool _Bool
#define true 1
#define false 0
#endif

// ADC base addresses
#define ADC1_BASE 0x40012000
#define ADC2_BASE 0x40012100
#define ADC3_BASE 0x40012200

// ADC channels
#define ADC_CHANNEL_0  0
#define ADC_CHANNEL_1  1
#define ADC_CHANNEL_2  2
#define ADC_CHANNEL_TEMP  16
#define ADC_CHANNEL_VREF  17

// ADC resolution
typedef enum {
    ADC_RES_12BIT = 0,
    ADC_RES_10BIT = 1,
    ADC_RES_8BIT = 2,
    ADC_RES_6BIT = 3
} adc_resolution_t;

// ADC configuration
typedef struct {
    uint32_t base_address;
    adc_resolution_t resolution;
    uint8_t sample_time;
    bool continuous_mode;
    bool dma_enable;
} adc_config_t;

// Function declarations
int adc_init(adc_config_t* config);
void adc_start_conversion(uint32_t adc_base);
void adc_stop_conversion(uint32_t adc_base);
uint16_t adc_read_channel(uint32_t adc_base, uint8_t channel);
bool adc_conversion_complete(uint32_t adc_base);
float adc_to_voltage(uint16_t adc_value, float vref);

// Multi-channel functions
void adc_configure_channels(uint32_t adc_base, uint8_t* channels, uint8_t count);
int adc_read_multiple(uint32_t adc_base, uint16_t* results, uint8_t count);

#endif // ADC_H
