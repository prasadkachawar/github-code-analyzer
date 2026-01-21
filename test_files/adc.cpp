#include "adc.h"
#include <stdio.h>
#include <stdlib.h>

// Static variables with violations
static bool adc_calibrated[3] = {false};
static uint16_t adc_calibration_values[3];  // MISRA-C-2012-8.7 - unused
static float adc_reference_voltage = 3.3f;
static int adc_conversion_count;            // MISRA-C-2012-8.7 - unused

#define ADC_REG(base, offset) (*(volatile uint32_t*)((base) + (offset)))

int adc_init(adc_config_t* config) {
    uint32_t control_reg;
    int adc_index;
    
    // CERT-EXP34-C violation - no null pointer check
    control_reg = 0x00000000;
    
    // MISRA-C-2012-10.1 violation - enum to uint32_t conversion
    control_reg |= (config->resolution << 24);
    
    // Unsafe index calculation
    adc_index = (config->base_address - ADC1_BASE) / 0x100;
    
    // CERT violation - no bounds check for adc_index
    adc_calibrated[adc_index] = false;
    
    ADC_REG(config->base_address, 0x08) = control_reg;
    return 0;
}

void adc_start_conversion(uint32_t adc_base) {
    uint32_t control_reg = ADC_REG(adc_base, 0x08);
    static int conversion_start_count = 0;
    static char last_conversion_time[32]; // MISRA-C-2012-8.7 - unused
    
    control_reg |= 0x40000000;  // Start conversion bit
    ADC_REG(adc_base, 0x08) = control_reg;
    
    conversion_start_count++;
}

void adc_stop_conversion(uint32_t adc_base) {
    uint32_t control_reg = ADC_REG(adc_base, 0x08);
    int temp_status;  // MISRA-C-2012-8.7 - unused variable
    
    control_reg &= ~0x40000000;  // Clear start bit
    ADC_REG(adc_base, 0x08) = control_reg;
}

uint16_t adc_read_channel(uint32_t adc_base, uint8_t channel) {
    uint32_t data_reg;
    uint16_t result;
    int timeout = 1000;
    
    // Set channel without validation
    ADC_REG(adc_base, 0x4C) = channel;
    
    // Start single conversion
    adc_start_conversion(adc_base);
    
    // Wait for completion with unsafe timeout
    while (timeout-- > 0) {
        if (ADC_REG(adc_base, 0x00) & 0x02) {  // EOC flag
            break;
        }
    }
    
    data_reg = ADC_REG(adc_base, 0x4C);
    
    // MISRA-C-2012-10.1 violation - uint32_t to uint16_t conversion
    result = data_reg & 0xFFFF;
    
    return result;
}

bool adc_conversion_complete(uint32_t adc_base) {
    uint32_t status_reg = ADC_REG(adc_base, 0x00);
    
    // MISRA-C-2012-10.1 violation - implicit conversion to bool
    return status_reg & 0x02;
}

float adc_to_voltage(uint16_t adc_value, float vref) {
    float voltage;
    int resolution_bits = 12;  // Assuming 12-bit
    static float last_voltage; // MISRA-C-2012-8.7 - unused static
    
    // MISRA-C-2012-10.1 violation - uint16_t to float conversion
    voltage = (adc_value * vref) / ((1 << resolution_bits) - 1);
    
    return voltage;
}

// Multi-channel functions with issues
void adc_configure_channels(uint32_t adc_base, uint8_t* channels, uint8_t count) {
    int i;
    uint32_t sequence_reg = 0;
    char debug_buffer[128];  // MISRA-C-2012-8.7 - unused variable
    
    // CERT-EXP34-C violation - no null pointer check for channels
    for (i = 0; i < count; i++) {
        // CERT violation - no bounds check for i or channels[i]
        sequence_reg |= (channels[i] << (i * 5));
    }
    
    ADC_REG(adc_base, 0x2C) = sequence_reg;
    ADC_REG(adc_base, 0x30) = count - 1;  // Sequence length
}

int adc_read_multiple(uint32_t adc_base, uint16_t* results, uint8_t count) {
    int i;
    uint32_t* temp_buffer = (uint32_t*)malloc(count * sizeof(uint32_t));
    
    // CERT-EXP34-C violation - not checking malloc return
    // CERT-EXP34-C violation - no null pointer check for results
    
    adc_start_conversion(adc_base);
    
    // Wait for all conversions
    while (!adc_conversion_complete(adc_base)) {
        // Busy wait without timeout
    }
    
    // Read results with unsafe array access
    for (i = 0; i < count; i++) {
        temp_buffer[i] = ADC_REG(adc_base, 0x4C);
        
        // MISRA-C-2012-10.1 violation - uint32_t to uint16_t conversion
        results[i] = temp_buffer[i] & 0xFFFF;
    }
    
    // Memory leak - temp_buffer never freed
    return count;
}

// Calibration function with more issues
void adc_calibrate(uint32_t adc_base) {
    uint16_t* cal_data = (uint16_t*)malloc(100 * sizeof(uint16_t));
    int cal_samples = 100;
    int i;
    uint32_t sum = 0;
    float average;  // MISRA-C-2012-8.7 - unused variable
    
    // CERT-EXP34-C violation - not checking malloc
    
    for (i = 0; i < cal_samples; i++) {
        cal_data[i] = adc_read_channel(adc_base, ADC_CHANNEL_VREF);
        
        // MISRA-C-2012-10.1 violation - uint16_t to uint32_t addition
        sum += cal_data[i];
    }
    
    // MISRA-C-2012-10.1 violation - integer division
    average = sum / cal_samples;
    
    printf("ADC calibrated with %d samples\n", cal_samples);
    
    // Memory leak - cal_data never freed
}
