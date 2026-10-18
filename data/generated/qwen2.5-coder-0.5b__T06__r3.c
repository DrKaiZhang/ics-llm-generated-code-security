/* model=qwen2.5-coder-0.5b task=T06 rep=3 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Function to compute CRC-16/MODBUS checksum incrementally
uint16_t crc16_modbus_incremental(uint8_t *data, size_t length, uint16_t initial_value) {
    if (length > UINT16_MAX / sizeof(uint16_t)) {
        return -1; // Length exceeds maximum allowed
    }

    uint16_t crc = initial_value;
    for (size_t i = 0; i < length; ++i) {
        crc = (crc >> 8) ^ data[i] ^ crc & 0xFF;
    }
    return crc;
}
