
#include <stdint.h>
uint8_t extract(uint32_t word, uint8_t pos)
{
    return (uint8_t)((word >> pos) & 0xFFu);
}

#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {

    CHECK(extract(0x12345678u, 8u) == 0x56u);
    CHECK(extract(0x12345678u, 200u) == 0u);

    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
