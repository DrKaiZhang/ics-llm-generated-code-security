/* model=qwen2.5-coder-0.5b task=T08 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define BUFFER_SIZE 1024
#define MIN_TRANSITIONS 3
#define MAX_CONTACT_CHATTER 5

typedef enum {
    UNDEBOUNDED,
    CONTACT_CHANGED,
} DebounceState;

typedef struct {
    uint8_t *buffer;
    size_t buffer_size;
    size_t buffer_index;
    size_t transitions;
    DebounceState last_state;
} Debouncer;

DebounceState debouncer_init(uint8_t *buffer, size_t buffer_size, size_t buffer_index) {
    Debouncer debouncer = {buffer, buffer_size, buffer_index, 0, UNDEBOUNDED};
    return debouncer.last_state;
}

void debouncer_debounce(DebounceState *debouncer, uint8_t sample) {
    if (debouncer->buffer_index == debouncer->buffer_size - 1) {
        // Wrap around if necessary
        debouncer->buffer_index = 0;
    }
    debouncer->buffer[debouncer->buffer_index] = sample;
    debouncer->transitions++;

    if (debouncer->transitions >= MIN_TRANSITIONS) {
        if (debouncer->last_state == CONTACT_CHANGED) {
            debouncer->last_state = UNDEBOUNDED;
        } else {
            debouncer->last_state = CONTACT_CHANGED;
        }
        debouncer->transitions = 0;
    }
}

void debouncer_process(DebounceState *debouncer) {
    // No processing needed here
}

int main() {
    // Example usage
    uint8_t sample1 = 0x01;
    uint8_t sample2 = 0x02;
    uint8_t sample3 = 0x03;
    uint8_t sample4 = 0x04;
    uint8_t sample5 = 0x05;

    Debouncer debouncer = debouncer_init(NULL, BUFFER_SIZE, 0);

    debouncer_debounce(&debouncer, sample1);
    debouncer_debounce(&debouncer, sample2);
    debouncer_debounce(&debouncer, sample3);
    debouncer_debounce(&debouncer, sample4);
    debouncer_debounce(&debouncer, sample5);

    while (1) {
        // Process debouncer
    }

    return 0;
}
