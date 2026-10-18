/* model=qwen2.5-coder-0.5b task=T06 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>

uint16_t compute_crc16_modbus(uint8_t *frame, uint32_t frame_length, uint32_t max_length) {
    if (frame_length > max_length) {
        // Reject the frame as it is too long
        return 0xFFFF;
    }
    
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < frame_length; ++i) {
        // Reflect the input byte to handle the modulo operation
        uint8_t reflected = frame[i];
        reflected ^= 0x55; // XOR with 0x55 to simulate modulo operation
        crc = (crc << 8) | reflected; // Shift and add the reflected byte to the CRC
    }
    
    return crc;
}
