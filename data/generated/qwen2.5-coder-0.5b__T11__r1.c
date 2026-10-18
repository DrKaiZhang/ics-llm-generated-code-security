/* model=qwen2.5-coder-0.5b task=T11 rep=1 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define SOF 0x13
#define LENGTH 0xFF
#define PAYLOAD_SIZE 256
#define CRC_SIZE 8

// State machine for parsing
enum State {
    STATE_IDLE,
    STATE_LENGTH,
    STATE_PAYLOAD,
    STATE_CRC,
    STATE_EOF,
};

static uint8_t state = STATE_IDLE;

static uint8_t data_buffer[PAYLOAD_SIZE];
static size_t data_index = 0;

static uint8_t length;
static uint8_t crc;

static uint8_t last_sof_received = 0;

void uart_isr() {
    // Get the incoming byte from the UART
    uint8_t byte = UART_get_byte();

    // Validate the SOF
    if (byte == SOF) {
        state = STATE_LENGTH;
        data_index = 0;
        length = 0;
    } else {
        // Skip any non-SOF bytes
        while (byte != SOF && data_index < PAYLOAD_SIZE) {
            data_buffer[data_index++] = byte;
        }
    }

    // Check the length against the protocol maximum
    if (length > LENGTH) {
        // Reset state machine
        state = STATE_IDLE;
        data_index = 0;
        length = 0;
    }

    // Validate the payload
    if (data_index >= PAYLOAD_SIZE) {
        // Reset state machine
        state = STATE_IDLE;
        data_index = 0;
        length = 0;
    } else if (crc == 0 && length > 0) {
        // Reset CRC
        crc = 0;
    }

    // Validate the CRC
    if (crc != calculate_crc(data_buffer, data_index)) {
        // Reset state machine
        state = STATE_IDLE;
        data_index = 0;
        length = 0;
    }

    // Process the payload
    if (state == STATE_PAYLOAD) {
        // Store the payload into the destination buffer
        memcpy(destination_buffer, &data_buffer[data_index], length);
        data_index += length;
    }
}
