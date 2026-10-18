/* model=qwen2.5-coder-0.5b task=T06 rep=0 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Function to compute CRC-16/MODBUS checksum over a protocol frame
uint16_t crc16_modbus(const uint8_t *frame, size_t length, size_t max_length) {
    if (length > max_length) {
        // Reject the frame length
        return 0xFFFF;
    }

    // Initialize the CRC value
    uint16_t crc = 0xFFFF;

    // Process each byte in the frame
    for (size_t i = 0; i < length; ++i) {
        // Add the current byte to the CRC
        crc ^= frame[i];

        // Update the CRC using the 0xA001 polynomial
        uint16_t poly = 0x0001;
        for (size_t j = 0; j < 8; ++j) {
            if ((crc & 0x0001) && (frame[i] & 1)) {
                poly ^= 0x2001;
            }
            crc >>= 1;
        }
    }

    return crc;
}

int main() {
    // Example usage
    uint8_t frame[] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09};
    size_t length = sizeof(frame);
    size_t max_length = 16;

    uint16_t checksum = crc16_modbus(frame, length, max_length);
    printf("CRC-16/MODBUS checksum: 0x%X\n", checksum);

    return 0;
}
