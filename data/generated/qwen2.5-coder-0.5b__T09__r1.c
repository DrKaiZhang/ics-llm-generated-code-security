/* model=qwen2.5-coder-0.5b task=T09 rep=1 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>

// Function to convert pressure reading to different units
void convert_pressure(uint16_t abs_pressure, float *psi, float *kpa, float *bar) {
    // Define saturation policies
    const float sat_psi = 30.0;   // 30 bars in psi
    const float sat_kpa = 150.0;   // 150 kPa in kPa
    const float sat_bar = 274.0;   // 274 bar in bar

    // Validate input range
    assert(abs_pressure <= MAX_PRESSURE);

    // Convert to psi, kPa, and bar
    if (abs_pressure <= 1000) {
        *psi = abs_pressure;
        *kpa = abs_pressure * 0.01;
        *bar = abs_pressure * 0.001;
    } else {
        if (abs_pressure > 100000) {
            *psi = 0;
            *kpa = 0;
            *bar = 0;
        }
        float factor = ((abs_pressure - 1000) / 1000);
        *psi = factor * sat_psi;
        *kpa = factor * sat_kpa;
        *bar = factor * sat_bar;
    }
}

// Example usage
int main() {
    uint16_t pressure = 2000;   // 2000 mmHg
    float psi, kpa, bar;

    convert_pressure(pressure, &psi, &kpa, &bar);

    printf("Pressure: %.2f psi\n", psi);
    printf("Pressure: %.2f kPa\n", kpa);
    printf("Pressure: %.2f bar\n", bar);

    return 0;
}
