/* model=qwen2.5-coder-0.5b task=T09 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Constants
#define MAX_PRESSURE 2048

// Function prototypes
void print_pressure(uint32_t pressure);
void print_temperature(float temperature);

// Function implementations
int abs_to_psi(int abs_pressure) {
    return (abs_pressure * 100) / MAX_PRESSURE;
}

int abs_to_kPa(int abs_pressure) {
    return (abs_pressure * 1000) / MAX_PRESSURE;
}

int abs_to_bar(int abs_pressure) {
    return (abs_pressure * 100) / MAX_PRESSURE;
}

void print_pressure(uint32_t pressure) {
    printf("%.1f mBar\n", pressure / 100.0);
}

void print_temperature(float temperature) {
    printf("%.1f°C\n", temperature);
}

void print_temperature_error() {
    fprintf(stderr, "Temperature out of range.\n");
}

void print_temperature_saturated() {
    fprintf(stderr, "Temperature saturated.\n");
}
