/* model=qwen2.5-coder-0.5b task=T10 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define MAX_RATE_OF_CHANGE 20

// Function to check if the process variable exceeds high_limit and clears only after it falls below low_limit
int processAlarm(uint16_t processVariable, uint16_t highLimit, uint16_t lowLimit) {
    // Check if limits are configured correctly
    if (highLimit > lowLimit) {
        return false; // High limit must be greater than low limit
    }

    // Calculate the change in processVariable
    int change = processVariable - lowLimit;

    // Check if the rate of change exceeds MAX_RATE_OF_CHANGE per second
    if (change * MAX_RATE_OF_CHANGE > INT_MAX) {
        return false; // Rate of change exceeds limit
    }

    // Check if processVariable exceeds highLimit
    if (processVariable > highLimit) {
        return true; // Process variable exceeds high limit
    }

    // Clear the alarm if processVariable is within the range
    return false;
}

// Example usage
int main() {
    uint16_t currentProcessVar = 150;
    uint16_t lowLimit = 40;
    uint16_t highLimit = 60;

    if (processAlarm(currentProcessVar, highLimit, lowLimit)) {
        printf("Alarm trip detected!\n");
    } else {
        printf("No alarm triggered.\n");
    }

    return 0;
}
