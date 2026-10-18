/* model=qwen2.5-coder-0.5b task=T06 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Function to compute CRC-16/MODBUS checksum using polynomial 0xA001
// Initial value is 0xFFFF
uint16_t crc16Modbus(const uint8_t* frame, size_t frameLength, size_t maxFrameSize) {
    uint16_t sum = 0xFFFF;
    size_t i;

    if (frameLength > maxFrameSize) {
        printf("Error: Frame length exceeds maximum frame size\n");
        return 0;
    }

    // Reflect input
    for (i = 0; i < frameLength; i++) {
        sum ^= frame[i];
        sum = (sum << 8) | frame[i + 1]; // Add the next byte to the sum
    }

    return sum;
}
