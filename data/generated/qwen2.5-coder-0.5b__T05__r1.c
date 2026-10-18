/* model=qwen2.5-coder-0.5b task=T05 rep=1 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Define the configuration for the Modbus RTU slave bank
#define MODBUS_SLAVE_BUFFER_SIZE 4096
#define REG_ADDR_MAX 0xFF

// Function to perform read-modify-write on the Modbus RTU slave bank
uint16_t write_modifiable(uint16_t* bank, uint16_t addr, uint16_t val, uint8_t mask) {
    // Check if the address is within the valid range
    if (addr > REG_ADDR_MAX || addr + 1 > REG_ADDR_MAX) {
        // Reject addresses that would straddle the end of the bank
        return 0;
    }

    // Check if the mask is valid
    if ((mask & ~0xFFFF) != 0) {
        // Reject mask values that are not valid for the current bank
        return 0;
    }

    // Check if the address is within the current bank
    if (addr < 0 || addr > REG_ADDR_MAX) {
        // Reject addresses that would straddle the end of the bank
        return 0;
    }

    // Calculate the number of bits to modify
    uint8_t num_bits = (val >> mask) & 0xFF;

    // Update the bank with the modified bits
    *bank |= (val >> mask) & 0xFF;
    *bank &= ~(val >> mask) & 0xFFFF;

    return num_bits;
}
