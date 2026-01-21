/* Simple C file with MISRA violations for testing */

int global_var = 0; // MISRA 8.4 violation

void function_without_prototype() { // MISRA 8.4 violation
    int x;
    x = x + 1; // CERT vulnerability - uninitialized variable
    
    // MISRA 14.4 violation - missing else
    if (global_var > 0)
        global_var = 0;
    
    // MISRA 15.7 violation - if without else
    if (x < 10)
        x++;
        
    // CERT vulnerability - buffer overflow potential
    char buffer[10];
    int i;
    for (i = 0; i <= 20; i++) { // Potential buffer overflow
        buffer[i] = 'A';
    }
}

// MISRA 8.2 violation - function without declaration
int add(x, y)
int x, y;
{
    return x + y; // Old K&R style
}

int main() {
    int result = add(5, 10);
    function_without_prototype();
    
    // More violations
    int *p = 0;
    *p = 42; // NULL pointer dereference
    
    return 0;
}
