/* model=qwen2.5-coder-0.5b task=T02 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define MIN_TEMP 20
#define MAX_TEMP 85

int adc_to_temp(uint16_t adc_reading) {
    // Convert ADC reading to 4-20mA using linear mapping
    int linear = (adc_reading - 128) * 4 / 20;

    // Apply offset correction
    int corrected_linear = linear + 40;

    // Check if the raw reading is within the acceptable range
    if (corrected_linear < MIN_TEMP || corrected_linear > MAX_TEMP) {
        return 0; // Return 0 if outside valid range
    }

    // Clamp the temperature to a safe operating range
    return clamp(corrected_linear, MIN_TEMP, MAX_TEMP);
}

int clamp(int value, int min, int max) {
    if (value < min) {
        return min;
    } else if (value > max) {
        return max;
    }
    return value;
}
