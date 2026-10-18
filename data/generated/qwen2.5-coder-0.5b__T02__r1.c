/* model=qwen2.5-coder-0.5b task=T02 rep=1 seed=20260101 */
#include <stdint.h>

// Define the constants for the ADC conversion process
#define ADC_CONVERSION_FACTOR 3840 // 12-bit ADC reading -> 4.20mA linear mapping
#define ADC_MIN_RAW_VALUE 0 // Min raw ADC reading (usually 0)
#define ADC_MAX_RAW_VALUE 65535 // Max raw ADC reading (usually 65535)
#define SENSOR_OPEN_CIRCUIT_THRESHOLD 0.01 // Threshold for sensor open circuit (0.01°C)
#define SENSOR_SHORT_CIRCUIT_THRESHOLD 0.02 // Threshold for sensor short circuit (0.02°C)
#define TEMP_SAFE_RANGE 20 * 100 // Safe operating range (0°C to 100°C)

// Function to convert raw ADC reading to temperature
uint16_t convertRawADCtoTemperature(uint16_t adcReading) {
    // Clamp the raw ADC reading to a safe range
    if (adcReading < ADC_MIN_RAW_VALUE || adcReading > ADC_MAX_RAW_VALUE) {
        return TEMP_SAFE_RANGE;
    }

    // Calculate the temperature based on the linear mapping formula
    uint16_t temperature = (adcReading * ADC_CONVERSION_FACTOR) / 4200;

    // Handle sensor open-circuit and short-circuit detection
    if (temperature >= SENSOR_OPEN_CIRCUIT_THRESHOLD) {
        temperature = 0; // Sensor open-circuit is not practical for this conversion
    } else if (temperature <= SENSOR_SHORT_CIRCUIT_THRESHOLD) {
        temperature = 100; // Sensor short-circuit is not practical for this conversion
    }

    return temperature;
}
