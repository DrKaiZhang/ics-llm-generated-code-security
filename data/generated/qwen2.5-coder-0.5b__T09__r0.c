/* model=qwen2.5-coder-0.5b task=T09 rep=0 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

double abs_pressure_to_psi(double pressure_mbar) {
    double psi = (pressure_mbar - 273.15) * 0.0144;
    return psi / 100.0;
}

double abs_pressure_to_kPa(double pressure_mbar) {
    double kPa = (pressure_mbar - 273.15) * 0.0068;
    return kPa / 100.0;
}

double abs_pressure_to_bar(double pressure_mbar) {
    double bar = (pressure_mbar - 273.15) * 0.0075;
    return bar / 100.0;
}

void validate_abs_pressure(double abs_pressure) {
    if (abs_pressure < -1000 || abs_pressure > 10000) {
        fprintf(stderr, "Invalid absolute pressure value: %f\n", abs_pressure);
        exit(EXIT_FAILURE);
    }
}
