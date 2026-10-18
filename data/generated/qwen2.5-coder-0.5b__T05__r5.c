/* model=qwen2.5-coder-0.5b task=T05 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

void modbus_write_register(uint8_t *addr, uint16_t value, uint16_t mask) {
    // Check for valid register address range
    if (addr + sizeof(mask) > 0xffff) {
        return; // Address out of range
    }

    // Ensure no unvalidated length is used
    if (addr + sizeof(value) != sizeof(modbus_message_t)) {
        return; // Value too large to fit in message
    }

    // Validate the mask
    if (mask == 0 || mask > 0xff) {
        return; // Mask out of range
    }

    // Calculate the start and end addresses
    uint16_t start = addr;
    uint16_t end = start + sizeof(modbus_message_t);

    // Read the current register value
    volatile uint16_t old_value;
    if (volatile int16_t (*modbus_read_register)(const void *addr, uint16_t *value, uint16_t mask) != NULL) {
        old_value = (*modbus_read_register)(addr, &value, mask);
    } else {
        return; // Unable to read register
    }

    // Update only the masked bits
    value &= ~mask; // Clear unwanted bits
    value |= mask; // Set new bits

    // Write the updated value back to the register
    if (volatile int16_t (*modbus_write_register)(const void *addr, uint16_t *value, uint16_t mask) != NULL) {
        (*modbus_write_register)(addr, &value, mask);
    } else {
        return; // Unable to write register
    }

    // Return the new register content
    *addr = old_value;
}
