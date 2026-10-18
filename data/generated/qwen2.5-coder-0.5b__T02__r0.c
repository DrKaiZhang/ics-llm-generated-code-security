/* model=qwen2.5-coder-0.5b task=T02 rep=0 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define ADC_RANGE 1023 // 12-bit ADC range

// Function to convert ADC reading to temperature
double adc_to_temperature(int adc_value) {
    int lower_bound = 140; // Lower bound of 4-20mA linear mapping
    int upper_bound = 156; // Upper bound
    int offset = 100; // Offset correction

    if (adc_value < lower_bound || adc_value > upper_bound) {
        return 0.0; // Return 0.0 if value is out of range
    }

    // Calculate temperature using the formula T = (A * V - B) / R
    int temp = (ADC_RANGE * adc_value - lower_bound) / (upper_bound - lower_bound);
    temp += offset;

    // Convert to deci-degrees Celsius
    double celsius = temp / 100.0;

    return celsius;
}

int main() {
    // Example usage
    int adc_value = 84; // Example ADC value
    double temp_celsius = adc_to_temperature(adc_value);
    printf("Temperature: %f°C\n", temp_celsius);
    return 0;
}
