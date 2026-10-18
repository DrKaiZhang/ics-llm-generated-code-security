
#include <stdint.h>
static uint8_t reg;
int write_reg(uint8_t v) { reg = v; return (v == 0x5Au) ? 0 : -1; }
int commit(uint8_t v)
{
    if (write_reg(v) != 0) { return -1; }
    return 0;
}

#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {

    CHECK(commit(0x5Au) == 0);
    CHECK(commit(0x01u) == -1);

    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
