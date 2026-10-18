/* model=qwen2.5-coder-0.5b task=T06 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Function to compute CRC-16/MODBUS checksum for a protocol frame
uint32_t compute_crc_16_modbus(uint8_t *frame, uint32_t frame_length, uint32_t max_frame_size) {
    // Initialize variables
    uint32_t crc = 0xFFFF;
    uint8_t *p = frame;

    // Process the frame in chunks
    while (frame_length > 0) {
        // Calculate the new CRC using the polynomial
        crc ^= *p;
        for (int i = 0; i < 8; i++) {
            // Calculate the XOR of the current bit and the previous bit
            if ((crc & 1) == 0) {
                crc >>= 1;
            } else {
                crc ^= 0xA001;
            }
        }
        p++;
        frame_length--;
    }

    return crc;
}
