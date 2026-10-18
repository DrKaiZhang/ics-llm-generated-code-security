/* model=qwen2.5-coder-0.5b task=T06 rep=1 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

uint16_t crc16_modbus(const uint8_t* frame, size_t frame_length, size_t max_size) {
    uint16_t crc = 0xFFFF;
    size_t index = 0;

    while (index < frame_length) {
        size_t bit_length = 8; // Assume each bit is 8 bits for simplicity

        // Read 8 bits from the frame and process them
        uint8_t byte = frame[index++];
        for (size_t i = 7; i >= 0; --i) {
            crc ^= ((byte >> i) & 1) << bit_length--;
        }

        // Shift the CRC forward by one bit and apply the polynomial
        crc <<= 1;
        if (crc > 0xFFFF) {
            crc ^= 0xA001; // Polynomial is 0x00A001 for MODBUS
        }
    }

    return crc;
}

int main() {
    uint8_t frame[] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF};
    size_t frame_length = sizeof(frame) / sizeof(frame[0]);
    size_t max_size = 10;

    uint16_t result = crc16_modbus(frame, frame_length, max_size);

    printf("CRC-16/MODBUS checksum: %u\n", result);
    return 0;
}
