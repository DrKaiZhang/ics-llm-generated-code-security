/* model=qwen2.5-coder-0.5b task=T02 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define ADC_MAX_VALUE 4095
#define ADC_MIN_VALUE -4095

uint32_t convert_adc_to_temp(uint16_t adc_reading) {
    uint32_t temp_celsius;

    // Apply standard 4-20 mA linear mapping
    uint32_t linear_mapping = (adc_reading - ADC_MIN_VALUE) * 4;
    temp_celsius = linear_mapping / 4 + 20;

    // Clamp the result to a safe operating range
    if (temp_celsius < -30) {
        temp_celsius = -30;
    } else if (temp_celsius > 70) {
        temp_celsius = 70;
    }

    return temp_celsius;
}

void handle_interrupt(void) {
    // Implement interrupt handling logic here
}
