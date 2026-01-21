/* Another simple C file with violations */

#define MAX_SIZE 100

typedef struct {
    int data[MAX_SIZE];
    int size;
} buffer_t;

static int counter; // MISRA 8.7 - could be local

// MISRA 16.4 violation - switch without break
int process_state(int state) {
    switch(state) {
    case 1:
        counter++;
    case 2: // Missing break - fall through
        counter += 2;
        break;
    default:
        counter = 0;
    }
    return counter;
}

// CERT vulnerability - race condition
void unsafe_increment() {
    static int shared_counter = 0;
    int temp = shared_counter; // Race condition
    temp++;
    shared_counter = temp;
}

// Buffer management with violations
int write_buffer(buffer_t* buf, int* data, int count) {
    int i;
    
    // No null pointer check - CERT violation
    for (i = 0; i < count; i++) {
        if (buf->size >= MAX_SIZE) {
            return -1;
        }
        buf->data[buf->size++] = data[i]; // Potential overflow
    }
    
    return 0;
}
