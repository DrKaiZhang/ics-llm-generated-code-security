
#include <stdint.h>
int32_t ratio(uint16_t raw, int16_t span, int16_t n)
{
    return ((int32_t)raw * (int32_t)span) / n;
}

#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {

    CHECK(ratio(100, 10, 4) == 250);
    CHECK(ratio(100, 10, 0) == 0);

    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
