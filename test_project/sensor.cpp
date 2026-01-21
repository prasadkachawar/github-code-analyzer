#include "sensor.h"
#include <stdio.h>

// Static variable that's never used - MISRA violation
static int calibration_data;

// Function with potential null pointer issues
SensorData* read_sensor_data(int sensor_id) {
    SensorData* data = (SensorData*)malloc(sizeof(SensorData));
    
    // CERT-EXP34-C violation - not checking malloc return value
    data->temperature = 25.5f;
    data->pressure = 1013.25f;
    data->humidity = 60.0f;
    data->sensor_id = sensor_id;
    
    return data;
}

// Function with inappropriate essential type usage
void process_sensor_reading(float reading) {
    int truncated_reading;
    
    // MISRA-C-2012-10.1 violation - float to int conversion without explicit cast
    truncated_reading = reading;
    
    if (truncated_reading > 100) {
        printf("High reading detected: %d\n", truncated_reading);
    }
}

// Function with unused static variables
static void calibrate_sensor() {
    static int calibration_count;  // Used
    static float last_calibration_value;  // MISRA-C-2012-8.7 - unused static
    
    calibration_count++;
    printf("Calibration #%d\n", calibration_count);
}

// Function with memory management issues
void sensor_cleanup(SensorData* data) {
    // CERT violation - potential use after free
    free(data);
    data->sensor_id = 0;  // Using freed memory
}
