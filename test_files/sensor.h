#ifndef SENSOR_H
#define SENSOR_H

#include <stdlib.h>

typedef struct {
    float temperature;
    float pressure;
    float humidity;
    int sensor_id;
} SensorData;

// Function declarations
SensorData* read_sensor_data(int sensor_id);
void process_sensor_reading(float reading);
void sensor_cleanup(SensorData* data);

#endif
