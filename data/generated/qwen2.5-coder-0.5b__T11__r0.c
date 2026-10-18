/* model=qwen2.5-coder-0.5b task=T11 rep=0 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define SOF 0x01
#define LEN 0x03
#define PAYLOAD 0x05
#define CRC 0x07
#define EOF 0x0B

#define MAX_PAYLOAD_SIZE 256

void uart_isr(void) {
    uint8_t byte = UART_Read();
    uint16_t length = (byte & 0xFF) << 8 | (byte >> 8);
    
    if (length == LEN) {
        // Validate payload length
        if (payload_length > MAX_PAYLOAD_SIZE) {
            UART_Print("Payload size exceeds buffer capacity\n");
            return;
        }
        
        // Copy payload to destination buffer
        memcpy(destination_buffer, &payload[0], payload_length);
        destination_buffer[payload_length] = 0; // Null terminator
        payload_length = 0;
    } else if (length == PAYLOAD) {
        // Process payload
        process_payload(payload);
    } else if (length == CRC) {
        // Process CRC
        process_crc(payload);
    } else {
        // Handle unexpected frame type
        UART_Print("Unrecognized frame type\n");
    }
}

void process_payload(uint8_t payload[]) {
    // Example processing
    printf("Received payload: ");
    for (int i = 0; i < payload_length; i++) {
        printf("%02X ", payload[i]);
    }
    printf("\n");
}

void process_crc(uint8_t payload[]) {
    // Example processing
    printf("Received CRC: %02X\n", payload[PAYLOAD]);
}
