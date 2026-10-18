
#include <stdint.h>
int16_t to_mA(int16_t pct)
{
    return (int16_t)(4000 + (pct * 16000) / 100);
}

#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {

    CHECK(to_mA(0) == 4000);
    CHECK(to_mA(100) == 20000);
    CHECK(to_mA(200) == 20000);

    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
