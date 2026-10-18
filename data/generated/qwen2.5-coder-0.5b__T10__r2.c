/* model=qwen2.5-coder-0.5b task=T10 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define HIGH_LIMIT 100
#define LOW_LIMIT 50

// Function to evaluate process-alarm condition
uint8_t processAlarmEvaluation(int processVariable, int lowLimit, int highLimit) {
    if (processVariable > highLimit) {
        return 0; // Alarm triggered
    } else if (processVariable < lowLimit) {
        return 1; // Alarm cleared
    } else {
        // High limit but low limit is lower
        return 2; // Hysteresis active
    }
}

// Example usage
int main() {
    uint8_t result = processAlarmEvaluation(125, HIGH_LIMIT, LOW_LIMIT);
    if (result == 0) {
        printf("Alarm triggered\n");
    } else if (result == 1) {
        printf("Alarm cleared\n");
    } else {
        printf("Hysteresis active\n");
    }
    return 0;
}
