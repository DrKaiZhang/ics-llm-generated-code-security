
#include <stdint.h>
static int32_t integ;
int16_t pid(int16_t setp, int16_t meas, int16_t kp, int16_t ki)
{
    int32_t err = (int32_t)setp - (int32_t)meas;
    integ = integ + ((int32_t)ki * err) / 100;
    if (integ > 32767) { integ = 32767; }
    if (integ < -32768) { integ = -32768; }
    return (int16_t)(((int32_t)kp * err) / 100 + integ);
}

#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {

    int i; int16_t y;
    for (i = 0; i < 50; i++) { y = pid(1000, 0, 100, 4000); }
    CHECK(y == 32767);

    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
