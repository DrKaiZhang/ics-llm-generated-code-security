
#include <stdint.h>
uint8_t g_duty;
void set_duty(int16_t cmd)
{
    g_duty = (uint8_t)cmd;
}

#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {

    set_duty(55);  CHECK(g_duty == 55);
    set_duty(250); CHECK(g_duty <= 100);

    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
