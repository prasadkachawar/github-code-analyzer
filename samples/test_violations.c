/* 
 * Sample C code with various MISRA and CERT violations
 * Used for testing the static analysis framework
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Global variable - potentially violates MISRA C:2012 Rule 8.7
int global_counter = 0;

// Function that only uses global_counter - should be local
void increment_counter(void) {
    global_counter++;
}

// CERT EXP34-C violation - potential null pointer dereference
void process_data(char* data) {
    // No null check before dereferencing
    int len = strlen(data);  // Potential null pointer dereference
    
    // MISRA C:2012 Rule 10.1 violation - mixed signed/unsigned
    unsigned int size = len;
    int index = size - 1;  // Mixing signed and unsigned
    
    // CERT ARR30-C violation - potential buffer overflow
    char buffer[10];
    strcpy(buffer, data);  // No bounds checking
    
    printf("Processed %d bytes\n", len);
}

// MISRA C:2012 Rule 16.4 violation - switch without default
void handle_state(int state) {
    switch (state) {
        case 0:
            printf("State 0\n");
            break;
        case 1:
            printf("State 1\n");
            break;
        // Missing default case
    }
}

// CERT EXP34-C - function returning potentially null pointer
char* allocate_buffer(size_t size) {
    char* buffer = malloc(size);
    // No null check on malloc result
    return buffer;
}

// More complex example with multiple violations
int process_array(int* arr, unsigned int count) {
    if (arr == NULL) {  // Good - null check present
        return -1;
    }
    
    // MISRA C:2012 Rule 10.1 - signed/unsigned comparison
    for (int i = 0; i < count; i++) {  // Mixing signed int with unsigned count
        // CERT ARR30-C - potential out of bounds access
        arr[i] = arr[i + 1];  // No bounds check for i+1
        
        // CERT EXP34-C - integer overflow potential
        int result = arr[i] * 1000000;  // Potential overflow
        printf("Result: %d\n", result);
    }
    
    return 0;
}

// Static variable example - should be compliant
static int file_scope_counter = 0;

void use_static_counter(void) {
    file_scope_counter++;
}

// Main function with various issues
int main(void) {
    char* data = allocate_buffer(100);
    // Using potentially null pointer without check
    process_data(data);  // CERT EXP34-C violation
    
    handle_state(2);  // Will hit missing default case
    
    int test_array[5] = {1, 2, 3, 4, 5};
    process_array(test_array, 10);  // Passing wrong size - buffer overflow
    
    free(data);
    return 0;
}
