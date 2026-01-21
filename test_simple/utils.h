/* Header file with violations */

#ifndef UTILS_H
#define UTILS_H

// MISRA 4.9 violation - function-like macro
#define MAX(a, b) ((a) > (b) ? (a) : (b))

// MISRA 2.3 violation - unused typedef
typedef int unused_type;

// Function declarations
extern int global_counter; // MISRA 8.7 potential violation

// MISRA 8.5 violation if used in multiple translation units
int inline_func(int x) {
    return x * 2;
}

// CERT recommendation violation - magic numbers
#define MAGIC_VALUE 0xDEADBEEF

void process_data(int* data, int size);

#endif /* UTILS_H */
