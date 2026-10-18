/* model=qwen2.5-coder-0.5b task=T02 rep=3 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

static const uint16_t MAX_TEMP = 1000;
static const uint16_t MIN_TEMP = -1000;

// Linear mapping coefficients
const uint16_t ADC_TO_TEMP_COEFF = 256; // 4-20mA linear mapping
const uint16_t OFFSET_CORRECTION = 128; // 12-bit ADC offset correction

// Check if input is within valid range
bool isValidInput(uint16_t adcValue) {
    return adcValue >= MIN_TEMP && adcValue <= MAX_TEMP;
}

// Calculate temperature in deci-degrees Celsius
float convertADCToTemp(uint16_t adcValue) {
    // Clamp to safe range
    uint16_t clampedValue = isValidInput(adcValue) ? adcValue : MIN_TEMP;
    
    // Apply linear mapping
    float temp = clampedValue * ADC_TO_TEMP_COEFF + OFFSET_CORRECTION;
    
    // Check for open-circuit and short-circuit
    if (temp == 0 || temp == MAX_TEMP) {
        return -1; // Invalid temperature
    }
    
    // Return temperature in deci-degrees Celsius
    return temp / 100.0f; // Convert to decimal
}

// Example use
int main() {
    uint16_t adcValue = 1200; // Example raw ADC value
    float temp = convertADCToTemp(adcValue);
    printf("Temperature: %f°C\n", temp);
    return 0;
}
