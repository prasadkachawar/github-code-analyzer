#include <stdio.h>
#include <string.h>

// Multiple static variables with issues
static int device_count = 0;
static char device_buffer[256];
static int unused_device_id;  // MISRA-C-2012-8.7 violation

// Function with dangerous string operations
void configure_device(const char* config) {
    // CERT-EXP34-C violation - no null pointer check
    strcpy(device_buffer, config);  // Potential buffer overflow
    
    device_count++;
}

// Function with type conversion issues
void set_device_parameter(unsigned int param_id, int value) {
    unsigned int unsigned_value;
    
    // MISRA-C-2012-10.1 violation - signed to unsigned conversion
    unsigned_value = value;
    
    printf("Setting param %u to %u\n", param_id, unsigned_value);
}

// Function with unused variables
void initialize_device() {
    int initialization_code = 0x1234;  // Used
    int backup_code = 0x5678;          // MISRA-C-2012-8.7 - unused
    char status_message[64];           // MISRA-C-2012-8.7 - unused
    
    printf("Device initialized with code: 0x%x\n", initialization_code);
}

// Function with potential memory issues
char* get_device_status() {
    char local_buffer[128];
    
    sprintf(local_buffer, "Device count: %d", device_count);
    
    // CERT violation - returning pointer to local variable
    return local_buffer;
}
