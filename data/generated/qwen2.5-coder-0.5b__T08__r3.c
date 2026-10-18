/* model=qwen2.5-coder-0.5b task=T08 rep=3 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Define the size of the debounced buffer
#define BUFFER_SIZE 1024

// Define the threshold for debounce
#define DEBOUNCE_THRESHOLD 300

// Initialize the debounced buffer
int debounced_buffer[BUFFER_SIZE] = {0};
uint8_t debounced_buffer_index = 0;
uint32_t debounced_state = 0;

// Function to perform debouncing
bool is_debounced(const uint32_t *samples, int samples_count) {
    // Calculate the number of consecutive identical samples
    int consecutive_identical_samples = 0;
    for (int i = 0; i < samples_count; ++i) {
        if (samples[i] == samples[(i + 1) % samples_count]) {
            consecutive_identical_samples++;
        } else {
            consecutive_identical_samples = 0;
        }
        // If there are N consecutive identical samples, update the state
        if (consecutive_identical_samples == DEBOUNCE_THRESHOLD) {
            debounced_state = 1;
            break;
        }
    }
    return debounced_state;
}

int main() {
    // Example sample data
    uint32_t samples[] = {100, 102, 105, 108, 109, 110, 112, 113, 116, 117, 118, 120};
    int samples_count = sizeof(samples) / sizeof(samples[0]);

    // Check if the debounced state has changed
    if (!is_debounced(samples, samples_count)) {
        printf("Contact chatter detected!\n");
    }

    return 0;
}
