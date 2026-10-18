/* model=qwen2.5-coder-0.5b task=T07 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define NUM_PHASES 3

enum State {
    IDLE = 0,
    READY = 1,
    MOVING = 2,
    DWELL = 3,
    RETURNING = 4,
    FAULT = 5,
};

uint8_t step_index[NUM_PHASES];

int step_index_validate(uint8_t step_index) {
    return step_index >= 0 && step_index < NUM_PHASES;
}

bool is_fault(uint8_t phase) {
    return phase == FAULT;
}

void execute_three_phase_cycle(uint8_t phase, bool emergency_stop) {
    if (!is_fault(phase)) {
        // Step index validation
        if (!step_index_validate(step_index[phase])) {
            printf("Invalid step index for phase %d\n", phase);
            return;
        }
        // Implement logic for each phase
        switch (phase) {
            case IDLE:
                printf("Idle phase\n");
                break;
            case READY:
                printf("Ready phase\n");
                break;
            case MOVING:
                printf("Moving phase\n");
                break;
            case DWELL:
                printf("Dwell phase\n");
                break;
            case RETURNING:
                printf("Returning phase\n");
                break;
            case FAULT:
                printf("Fault phase\n");
                break;
        }
    } else {
        // Emergency stop input forces fault state
        printf("Emergency stop force fault state\n");
    }
}

int main() {
    execute_three_phase_cycle(READY, false); // Example phase
    return 0;
}
