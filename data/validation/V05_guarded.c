
#include <stdint.h>
#define NB 8
static uint16_t slots[NB];
uint16_t get(uint8_t i)
{
    if (i >= NB) { return 0u; }
    return slots[i];
}

#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {

    int i;
    for (i = 0; i < NB; i++) { slots[i] = (uint16_t)(i * 2); }
    CHECK(get(3) == 6u);
    CHECK(get(200) == 0u);

    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
