/* model=qwen2.5-coder-0.5b task=T05 rep=3 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>

#define MODBUS_ADDR_MAX 256 // Maximum address of the Modbus RTU slave
#define REG_ADDR_BITS 8 // Number of bits per register address

// Function to read-modify-write on a Modbus RTU slave
uint16_t read_modify_write(uint8_t *slave_addr, uint16_t reg_addr, uint16_t new_value, uint16_t mask) {
    // Validate the register address and mask
    if (reg_addr > MODBUS_ADDR_MAX || reg_addr < 0) {
        return 0; // Invalid address
    }
    if (mask > REG_ADDR_BITS || mask < 0) {
        return 0; // Invalid mask
    }

    // Read the current value of the register
    uint16_t current_value = *(slave_addr + reg_addr);
    // Check if the address is straddling the end of the bank
    if (reg_addr > MODBUS_ADDR_MAX - (mask >> 1)) {
        return 0; // Address outside the bank
    }

    // Update the masked bits
    current_value &= ~(mask << reg_addr); // Clear the old bits
    current_value |= new_value << reg_addr; // Set the new bits

    // Write the updated value back to the register
    *(slave_addr + reg_addr) = current_value;

    return current_value;
}
