
#include <stdint.h>
/* updated from a 1 kHz control ISR under a critical section */
static void disable_irq(void);
static void enable_irq(void);
static volatile int32_t total;
int32_t add(int32_t v)
{
    int32_t prev;
    disable_irq();
    prev = total;
    total = prev + v;
    enable_irq();
    return total;
}
static void disable_irq(void) { }
static void enable_irq(void) { }

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
