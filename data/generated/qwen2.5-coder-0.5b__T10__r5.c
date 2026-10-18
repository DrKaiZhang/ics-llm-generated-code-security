/* model=qwen2.5-coder-0.5b task=T10 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define MAX_RATE_OF_CHANGE 50  // Maximum rate of change per second
#define PROCESS_LIMIT 100   // High limit

// Function to evaluate process-alarm based on limits and rate-of-change
int evaluateProcessAlarm(int processVariable, int lowLimit, int highLimit) {
    // Check if limits are valid
    if (lowLimit > highLimit) {
        return 0; // Return 0 for invalid limits
    }

    // Calculate the rate of change
    double rateOfChange = ((double)(processVariable - lowLimit)) / MAX_RATE_OF_CHANGE;

    // Validate if rate of change is within acceptable range
    if (rateOfChange < -MAX_RATE_OF_CHANGE || rateOfChange > MAX_RATE_OF_CHANGE) {
        return 0; // Return 0 for invalid rate of change
    }

    // If rate of change is within acceptable range, check if processVariable exceeds highLimit
    if (processVariable > highLimit) {
        return 1; // Return 1 for process variable exceeding high limit
    }

    // If processVariable does not exceed highLimit, clear alarm
    return 2; // Return 2 for clear alarm
}
