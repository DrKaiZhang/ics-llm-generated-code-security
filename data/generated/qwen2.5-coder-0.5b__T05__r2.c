/* model=qwen2.5-coder-0.5b task=T05 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

uint16_t update_register_modbus(uint8_t *ptr, uint16_t addr, uint16_t value, uint16_t mask) {
    if (addr >= MAX_ADDRESS || addr + 16 > MAX_ADDRESS) {
        return 0; // Out-of-bounds access or mask
    }
    if (addr < 0) {
        return 0; // Invalid register address
    }
    
    // Read the current register value
    uint16_t current_value = *(ptr + addr);
    // Apply the mask
    current_value &= mask;
    // Update the register value with the new value
    *ptr + addr = current_value;
    return current_value;
}
