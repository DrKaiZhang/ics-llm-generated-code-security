/* model=qwen2.5-coder-0.5b task=T09 rep=3 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

double convert_absolute_pressure(int absPressure) {
    if (absPressure > 10000) {
        fprintf(stderr, "Error: Absolute pressure exceeds limit of 10000 mmHg\n");
        return -1.0; // Indicate error or handle appropriately
    }
    
    double pressure = absPressure / 100.0;
    pressure *= 338.2; // Convert bar to psi
    pressure *= 100.0; // Convert kPa to psi

    return pressure;
}
