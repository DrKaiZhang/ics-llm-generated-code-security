/* model=qwen2.5-coder-0.5b task=T08 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define BUFFER_SIZE 100
#define SAMPLE_RATE 100

// Define the debounce logic function
void debounce(uint8_t *samples, int sample_count, uint8_t *debounced, int debounced_count) {
    // Initialize the debounced buffer with zeros
    for (int i = 0; i < debounced_count; i++) {
        debounced[i] = 0;
    }

    // Check each sample to determine if it has changed from the last one
    for (int i = 0; i < sample_count; i++) {
        if (samples[i] != samples[(i + 1) % sample_count]) {
            // Count the transitions to expose contact chatter
            debounced[debounced_count - 1]++;
        }
    }
}

// Main function to handle the debouncing process
int main() {
    uint8_t samples[BUFFER_SIZE];
    uint8_t debounced[BUFFER_SIZE];

    int sample_count = 0;
    uint8_t debounced_count = 0;
    uint8_t prev_sample = 0;

    while (true) {
        // Read the current sample
        int current_sample = samples[sample_count];

        // Update the debounced buffer
        if (current_sample != prev_sample) {
            debounce(samples, sample_count, debounced, debounced_count);
        }

        // Update the previous sample
        prev_sample = current_sample;

        // Increment the sample counter
        sample_count++;

        // Check if we have enough samples for a debounce
        if (sample_count >= BUFFER_SIZE && debounced[debounced_count - 1] > 0) {
            // Expose contact chatter
            printf("Contact chatter detected!\n");
        }

        // Wait for a short period of time
        // This is just to simulate real-time processing
        sleep(100); // Sleep for 1 second
    }

    return 0;
}
