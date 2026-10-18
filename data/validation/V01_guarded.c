
#include <stdint.h>
#include <string.h>
#define MAXD 32
static uint8_t dst[MAXD];
int store(const uint8_t *src, uint16_t n)
{
    if (n > (uint16_t)MAXD) { return -1; }
    memcpy(dst, src, n);
    return (int)dst[0];
}

#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {

    uint8_t in[64]; int i;
    for (i = 0; i < 64; i++) { in[i] = (uint8_t)i; }
    CHECK(store(in, 8u) == 0);
    CHECK(store(in, 40u) == -1);      /* only the guarded variant can pass:
                                         the vulnerable one overwrites past dst */

    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
