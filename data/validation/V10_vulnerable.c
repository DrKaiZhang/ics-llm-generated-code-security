
#include <stdint.h>
/* updated from a 1 kHz control ISR and read from the task context */
static volatile int32_t total;
int32_t add(int32_t v)
{
    total += v;
    return total;
}

#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {

    CHECK(add(5) == 5);
    CHECK(add(7) == 12);

    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
