/* model=qwen2.5-coder-0.5b task=T08 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define SAMPLE_RATE 100 // Sampling rate (Hz)
#define WINDOW_SIZE 100 // Number of consecutive identical samples for contact chatter
#define BUFFER_SIZE 64 // Size of the buffer (rounded up by sampling rate)

typedef uint8_t sample_t;

int debouncer(sample_t *samples, size_t buffer_size, size_t window_size, int samples_per_window) {
    int transitions = 0;
    int current_index = 0;
    int prev_index = 0;

    while (current_index < buffer_size) {
        if ((prev_index = current_index - WINDOW_SIZE) < 0) {
            prev_index = buffer_size - WINDOW_SIZE;
        }

        if (samples[current_index] != samples[prev_index]) {
            transitions++;
        }

        current_index++;
    }

    return transitions;
}

int main() {
    sample_t samples[BUFFER_SIZE];
    size_t window_size = WINDOW_SIZE;
    int samples_per_window = samples_per_window;
    int result = debouncer(samples, BUFFER_SIZE, window_size, samples_per_window);
    printf("Contact chatter: %d\n", result);
    return 0;
}
