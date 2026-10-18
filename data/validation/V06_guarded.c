
#include <stdint.h>
#define CAP 64
static uint8_t sum(const uint8_t *b, uint16_t n)
{
    uint16_t i; uint8_t s = 0;
    if (n > CAP) { return 0u; }
    for (i = 0; i < n; i++) { s = (uint8_t)(s + b[i]); }
    return s;
}

#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {

    uint8_t b[16]; int i;
    for (i = 0; i < 16; i++) { b[i] = 1u; }
    CHECK(sum(b, 4u) == 4u);

    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
