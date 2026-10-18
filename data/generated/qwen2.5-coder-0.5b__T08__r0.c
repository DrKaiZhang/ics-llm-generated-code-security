/* model=qwen2.5-coder-0.5b task=T08 rep=0 seed=20260101 */
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

#define BUFFER_SIZE 100
#define MIN_CONTACT_CHATTER 2

typedef struct {
    uint8_t samples[BUFFER_SIZE];
    int index;
} Debouncer;

void debounce(const unsigned char* samples, const int samples_size, Debouncer* debouncer) {
    if (debouncer == NULL || samples == NULL || samples_size <= 0) {
        return;
    }

    debouncer->index = 0;
    int contact_chatter_count = 0;

    while (debouncer->index < samples_size - 1) {
        int current_sample = samples[debouncer->index];
        int next_sample = samples[debouncer->index + 1];

        if (current_sample != next_sample) {
            contact_chatter_count++;
            if (contact_chatter_count >= MIN_CONTACT_CHATTER) {
                break;
            }
        }

        debouncer->index++;
    }

    debouncer->index %= BUFFER_SIZE;
}

int main() {
    unsigned char samples[] = {0x55, 0xAA, 0x33, 0x66, 0xDD, 0xFF, 0x44, 0xBB, 0xCC, 0xDD};
    int samples_size = sizeof(samples) / sizeof(samples[0]);

    Debouncer debouncer;
    debounce(samples, samples_size, &debouncer);

    // Output debounced state
    printf("Debounced state: ");
    for (int i = 0; i < BUFFER_SIZE; i++) {
        printf("%d ", debouncer.samples[i]);
    }
    printf("\n");

    return 0;
}
