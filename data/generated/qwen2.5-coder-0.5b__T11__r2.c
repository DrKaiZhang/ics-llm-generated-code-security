/* model=qwen2.5-coder-0.5b task=T11 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define SOF 0x55
#define LENGTH 4
#define PAYLOAD_SIZE 100

// Initialize the parser state
bool parser_state = false;
uint8_t current_length = 0;
uint8_t current_payload[LENGTH];

// UART ISR function
void uart_isr(void) {
    uint8_t received_byte = UART_Read(); // Read one byte from UART
    if (received_byte == SOF) { // Start of frame
        parser_state = true;
        current_length = LENGTH; // Reset the length
    } else if (received_byte == LENGTH) { // Length byte
        // Validate length
        if (current_length == LENGTH && parser_state) {
            current_payload[current_length - 1] = received_byte;
            parser_state = false; // Wait for payload
            // Reset length
            current_length = 0;
        }
    } else if (parser_state) { // Payload byte
        // Validate payload
        if (parser_state) {
            current_payload[current_length - 1] = received_byte;
            current_length++;
            // Check if payload is complete
            if (current_length == LENGTH) {
                // Resynchronize to the next SOF
                while (!uart_read()) {
                    // Wait for data
                }
                received_byte = UART_Read();
                if (received_byte != SOF) {
                    // Malformed frame
                    // Reset state machine
                    parser_state = false;
                    current_length = 0;
                }
            }
        }
    }
}
