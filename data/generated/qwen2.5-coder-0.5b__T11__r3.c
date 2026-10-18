/* model=qwen2.5-coder-0.5b task=T11 rep=3 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define SOF 0x55
#define LENGTH 8
#define PAYLOAD_SIZE 16

// State machine states
enum {
    IDLE = 0,
    LENGTH_VALIDATION = 1,
    PAYLOAD_VALIDATION = 2,
    CRC_VALIDATION = 3,
    END_OF_FRAME = 4,
    OVERFLOW = 5,
    TIMEOUT = 6,
};

// State machine variables
uint8_t state = IDLE;
uint8_t length = 0;
uint8_t payload_size = 0;
uint8_t buffer[PAYLOAD_SIZE];
bool crc_valid = false;

void uart_isr(void) {
    uint8_t received_byte = uart_get_char();
    
    // Validate SOF
    if (received_byte == SOF) {
        state = LENGTH_VALIDATION;
    }
    
    // Validate length
    if (state == LENGTH_VALIDATION && received_byte <= LENGTH) {
        length = received_byte;
        
        // Validate payload size
        if (state == LENGTH_VALIDATION && payload_size + received_byte > PAYLOAD_SIZE) {
            state = PAYLOAD_VALIDATION;
        }
        
        // Validate CRC
        if (state == PAYLOAD_VALIDATION && crc_valid) {
            state = CRC_VALIDATION;
        }
        
        // Check if we have reached the end of a frame
        if (state == CRC_VALIDATION && received_byte == '\n') {
            state = END_OF_FRAME;
        }
    }
    
    // Check for overflow
    if (state == OVERFLOW) {
        // Handle overflow logic here
    }
    
    // Check for timeout
    if (state == TIMEOUT) {
        // Handle timeout logic here
    }
}

void process_frame(uint8_t* data, size_t data_size) {
    switch (state) {
        case IDLE:
            // Reset state machine on invalid SOF
            break;
        case LENGTH_VALIDATION:
            // Process length validation
            break;
        case PAYLOAD_VALIDATION:
            // Process payload validation
            break;
        case CRC_VALIDATION:
            // Process CRC validation
            break;
        case END_OF_FRAME:
            // Process end of frame
            break;
        case OVERFLOW:
            // Handle overflow logic here
            break;
        case TIMEOUT:
            // Handle timeout logic here
            break;
    }
}
