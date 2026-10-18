/* model=qwen2.5-coder-0.5b task=T12 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Function to step a stepper motor through a speed ramp
void StepperStep(uint8_t ramp_position, uint16_t* steps, int delay_ms, bool direction, void (*step_output)(uint8_t)) {
    if (ramp_position < 0 || ramp_position >= sizeof(steps) / sizeof(steps[0]) - 1) {
        // Return if ramp position is out of range
        return;
    }

    if (direction) {
        // Step forward (incrementing)
        steps[ramp_position]++;
    } else {
        // Step backward (decrementing)
        steps[ramp_position]--;
    }

    // Delay for the specified amount of time
    for (int i = 0; i < delay_ms; i++) {
        step_output(ramp_position);
        // Add a small delay to avoid interrupt interruptions
        __builtin_usleep(10);
    }
}
