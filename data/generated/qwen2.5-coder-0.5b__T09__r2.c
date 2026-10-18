/* model=qwen2.5-coder-0.5b task=T09 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Function to convert absolute pressure to different scales
void pressure_convert(int absolute_pressure, double* psi, double* kPa, double* bar) {
    // Check for valid absolute pressure input
    if (absolute_pressure < -10000 || absolute_pressure > 10000) {
        fprintf(stderr, "Pressure out of range. Must be between -10000 and 10000 mmbar.\n");
        return;
    }

    // Convert to psi
    psi[0] = absolute_pressure / 100;

    // Convert to kPa
    kPa[0] = (absolute_pressure - 37.2738) / 0.25;

    // Convert to bar
    bar[0] = absolute_pressure / 100000;
}

int main() {
    int abs_pressure = 4500; // Example absolute pressure in mmbar
    double psi, kPa, bar;

    pressure_convert(abs_pressure, &psi, &kPa, &bar);

    printf("Absolute Pressure: %d mmbar\n", abs_pressure);
    printf("PSI: %.1f psi\n", psi);
    printf("KPA: %.1f kPa\n", kPa);
    printf("Bar: %.1f bar\n", bar);

    return 0;
}
