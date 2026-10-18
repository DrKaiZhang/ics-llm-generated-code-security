/* model=qwen2.5-coder-0.5b task=T10 rep=3 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define MAX_RATE_OF_CHANGE 10

// Define a function to evaluate the alarm
uint8_t evaluate_process_alarm(uint32_t process_variable, uint32_t high_limit, uint32_t low_limit) {
    // Validate limits
    if (low_limit > high_limit) {
        printf("Invalid limits: low_limit (%u) is greater than high_limit (%u)\n", low_limit, high_limit);
        return 0; // Return invalid alarm code
    }

    uint32_t rate_of_change = ((process_variable - low_limit) / (MAX_RATE_OF_CHANGE * 1000));

    // Evaluate alarm
    if (rate_of_change > 0 && rate_of_change < 1) {
        return 1; // Alarm trip
    } else {
        return 0; // No alarm trip
    }
}
