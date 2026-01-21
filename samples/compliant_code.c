/*
 * Clean C code that should pass static analysis
 * Used as a reference for compliant code
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Static variable - file scope is appropriate
static int module_counter = 0;

// Local helper function
static void increment_module_counter(void) {
    module_counter++;
}

// Function with proper null checking
int safe_string_length(const char* str) {
    if (str == NULL) {
        return -1;  // Error indication
    }
    
    return (int)strlen(str);
}

// Safe buffer processing with bounds checking
int safe_buffer_copy(char* dest, size_t dest_size, const char* src) {
    if (dest == NULL || src == NULL || dest_size == 0) {
        return -1;  // Error - invalid parameters
    }
    
    size_t src_len = strlen(src);
    if (src_len >= dest_size) {
        return -2;  // Error - insufficient space
    }
    
    strcpy(dest, src);  // Safe because we checked bounds
    return 0;  // Success
}

// Switch statement with default case
void handle_command(int cmd) {
    switch (cmd) {
        case 0:
            printf("Initialize\n");
            break;
        case 1:
            printf("Execute\n");
            break;
        case 2:
            printf("Terminate\n");
            break;
        default:
            printf("Unknown command\n");
            break;
    }
}

// Safe memory allocation with error checking
char* safe_allocate_buffer(size_t size) {
    if (size == 0) {
        return NULL;  // Invalid size
    }
    
    char* buffer = malloc(size);
    if (buffer == NULL) {
        printf("Memory allocation failed\n");
        return NULL;
    }
    
    // Initialize to ensure deterministic behavior
    memset(buffer, 0, size);
    return buffer;
}

// Array processing with proper bounds checking
int safe_process_array(const int* arr, size_t count) {
    if (arr == NULL || count == 0) {
        return -1;  // Invalid parameters
    }
    
    for (size_t i = 0; i < count; i++) {
        // Safe array access - i is guaranteed < count
        if (arr[i] > 0) {
            printf("Positive value at index %zu: %d\n", i, arr[i]);
        }
    }
    
    return 0;
}

// Function demonstrating local scope usage
void demonstrate_local_scope(void) {
    // Local variable - only used in this function
    int local_temp = 42;
    
    printf("Local value: %d\n", local_temp);
    
    increment_module_counter();
    printf("Module counter: %d\n", module_counter);
}

// Main function with proper error handling
int main(void) {
    const size_t BUFFER_SIZE = 100;
    char* buffer = safe_allocate_buffer(BUFFER_SIZE);
    
    if (buffer == NULL) {
        printf("Failed to allocate buffer\n");
        return 1;
    }
    
    const char* test_string = "Hello, World!";
    int result = safe_buffer_copy(buffer, BUFFER_SIZE, test_string);
    
    if (result == 0) {
        printf("Buffer content: %s\n", buffer);
        printf("String length: %d\n", safe_string_length(buffer));
    } else {
        printf("Buffer copy failed with code: %d\n", result);
    }
    
    // Test array processing
    int test_array[] = {1, -2, 3, -4, 5};
    size_t array_size = sizeof(test_array) / sizeof(test_array[0]);
    
    safe_process_array(test_array, array_size);
    
    // Test command handling
    for (int cmd = 0; cmd <= 3; cmd++) {
        handle_command(cmd);
    }
    
    demonstrate_local_scope();
    
    // Clean up
    free(buffer);
    
    return 0;
}
