/* model=qwen2.5-coder-0.5b task=T12 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Function prototype
void StepperRamp(uint8_t *table, uint32_t size, uint8_t rampPos, bool dir, StepperOutputCallback cb);

typedef struct {
    uint8_t *table;
    uint32_t size;
    uint8_t rampPos;
    bool dir;
    StepperOutputCallback cb;
} StepperState;

// Helper function to validate the ramp table and index
bool isValidRampTable(StepperState *state, uint8_t rampPos) {
    if (state->rampPos >= state->size || state->rampPos < 0) {
        return false;
    }
    return true;
}

// Main function to perform the stepper ramp
void StepperRamp(uint8_t *table, uint32_t size, uint8_t rampPos, bool dir, StepperOutputCallback cb) {
    StepperState state = {
        .table = table,
        .size = size,
        .rampPos = rampPos,
        .dir = dir,
        .cb = cb
    };

    // Validate the ramp table and index
    if (!isValidRampTable(&state, rampPos)) {
        return;
    }

    // Calculate the delay for each step in the ramp
    for (uint32_t i = 0; i < size; i++) {
        uint32_t stepTime = (table[i] + i) % 100; // Assuming steps are 100ms (4ms on average)
        uint32_t delay = (stepTime - 50) / 4; // Adjust for the ramp position

        if (state.dir) {
            cb(delay, i);
        } else {
            cb(i, delay);
        }
    }
}
