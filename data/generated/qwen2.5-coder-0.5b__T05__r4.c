/* model=qwen2.5-coder-0.5b task=T05 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>

// Define constants for Modbus RTU slave addresses
#define MODBUS_RTU_SLAVE_ADDRESS 0x03

// Function to read-modify-write on a Modbus RTU slave
uint16_t modify_register(uint16_t *slave_bank, uint16_t address, uint16_t value, uint8_t mask) {
    // Validate the address range
    if (address < MODBUS_RTU_SLAVE_ADDRESS || address > MODBUS_RTU_SLAVE_ADDRESS + 15) {
        assert(false); // Address out of range
    }

    // Validate the mask
    if (mask > 16) {
        assert(false); // Mask cannot exceed 16 bits
    }

    // Calculate the effective address
    uint16_t effective_address = address & ~(mask - 1);

    // Ensure the new value fits within the 16-bit limit
    if (value > 0xFFFF) {
        assert(false); // Value exceeds the 16-bit limit
    }

    // Attempt to modify the register
    *slave_bank = effective_address | value;

    // Return the new register content
    return *slave_bank;
}
