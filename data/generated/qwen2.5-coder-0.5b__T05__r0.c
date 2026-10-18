/* model=qwen2.5-coder-0.5b task=T05 rep=0 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

void update_register(ModbusRTU_slave* bank, uint16_t register_address, uint16_t value, uint8_t mask) {
    uint16_t old_value = bank->registers[register_address];
    uint16_t updated_value = (old_value & ~mask) | (value & mask);
    bank->registers[register_address] = updated_value;
}

uint16_t read_register(ModbusRTU_slave* bank, uint16_t register_address) {
    uint16_t old_value = bank->registers[register_address];
    return old_value;
}
