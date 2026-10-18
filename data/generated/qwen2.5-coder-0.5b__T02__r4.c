/* model=qwen2.5-coder-0.5b task=T02 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

static const uint8_t adc_offset = 4; // mV
static const uint8_t adc_max = 1023; // mV

int convert_adc_to_temperature(int adc_reading) {
    // Clamp the reading to within the safe range
    if (adc_reading < 0 || adc_reading > adc_max) {
        return 0; // Return 0 if reading is out of range
    }

    // Standard 4-20 mA linear mapping
    int temperature = (adc_reading - adc_offset) * 4 / 2000;

    // Check for open-circuit and short-circuit
    if (adc_reading == 0 || adc_reading == adc_max) {
        return 0; // Return 0 if sensor is open or short-circuits
    }

    // Apply offset correction
    return temperature;
}
