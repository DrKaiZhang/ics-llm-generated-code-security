/* model=qwen2.5-coder-0.5b task=T09 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define MAX_PRESSURE 100000  // Maximum absolute pressure value in mbar

// Function to convert absolute pressure to various units
void convertPressure(float pressure, char *unit) {
    if (pressure < 0) {
        // Apply saturation if the pressure is negative
        pressure = -pressure;
        if (pressure > MAX_PRESSURE) {
            *unit = 'F'; // For Fahrenheit units
            return;
        } else if (pressure >= 101372) {
            *unit = 'K'; // For Kelvin units
            return;
        }
    }

    float psi = pressure / 100000; // Convert mbar to psi
    float kPa = pressure / 1000;   // Convert mbar to kPa
    float bar = pressure / 100;     // Convert mbar to bar

    printf("%f %c\n", psi, unit[0]);  // Print formatted output
    printf("%f %c\n", kPa, unit[0]); // Print formatted output
    printf("%f %c\n", bar, unit[0]);  // Print formatted output
}

int main() {
    float absPressure = 50000;  // Example absolute pressure reading in mbar
    convertPressure(absPressure, "M");  // Convert to Mbar
    return 0;
}
