#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Global variables - MISRA violation
int global_counter;
static int unused_variable;  // MISRA-C-2012-8.7 violation - unused static variable

// Function with security issues
char* unsafe_string_copy(char* dest, const char* src) {
    // CERT-EXP34-C violation - potential null pointer dereference
    strcpy(dest, src);  // Unsafe string copy
    return dest;
}

// Function with type conversion issues  
void type_conversion_issues() {
    int signed_val = -1;
    unsigned int unsigned_val;
    
    // MISRA-C-2012-10.1 violation - inappropriate type conversion
    unsigned_val = signed_val;  
    
    printf("Value: %u\n", unsigned_val);
}

// Function with unused parameters
void function_with_unused_params(int used_param, int unused_param) {
    // Only using one parameter - MISRA violation
    printf("Using only: %d\n", used_param);
}

// Main function with multiple issues
int main() {
    char buffer[10];
    char* large_string = "This is a very long string that will overflow the buffer";
    
    // Buffer overflow risk - CERT violation
    unsafe_string_copy(buffer, large_string);
    
    // Using global variable without initialization
    global_counter++;
    
    // Calling function with type issues
    type_conversion_issues();
    
    // Calling function with unused parameters
    function_with_unused_params(42, 99);
    
    // Missing return statement validation
    printf("Buffer: %s\n", buffer);
    printf("Counter: %d\n", global_counter);
    
    return 0;
}
