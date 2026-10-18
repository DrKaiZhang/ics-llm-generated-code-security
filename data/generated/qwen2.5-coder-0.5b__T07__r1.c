/* model=qwen2.5-coder-0.5b task=T07 rep=1 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define NUM_STEPS 4

enum ActuatorState {
    IDLE,
    READY,
    MOVING,
    DWELL,
    RETURNING,
    FAULT
};

struct ActuatorStateTransition {
    enum ActuatorState next;
    size_t step_index;
};

struct ActuatorStateMachine {
    enum ActuatorState current_state;
    struct ActuatorStateTransition transitions[NUM_STEPS];
};

void setup_actuator_states(struct ActuatorStateMachine *state_machine) {
    // Initialize the current state to IDLE
    state_machine->current_state = IDLE;

    // Initialize the transitions
    for (size_t i = 0; i < NUM_STEPS; i++) {
        state_machine->transitions[i].next = FAULT;
        state_machine->transitions[i].step_index = i;
    }
}

bool check_transition(struct ActuatorStateMachine *state_machine, size_t step_index) {
    return step_index < NUM_STEPS && state_machine->transitions[step_index].next != FAULT;
}

void execute_actuator(struct ActuatorStateMachine *state_machine, int32_t input) {
    // Check if the current state is IDLE
    if (state_machine->current_state == IDLE) {
        // If input is 0, move to the READY state
        if (input == 0) {
            state_machine->current_state = READY;
        } else {
            // If input is not 0, set the FAULT state
            state_machine->current_state = FAULT;
        }
    } else {
        // If the current state is READY or MOVING, skip the next state
        if (state_machine->current_state == READY || state_machine->current_state == MOVING) {
            step_index++;
        }
    }
}

int main() {
    struct ActuatorStateMachine state_machine;

    setup_actuator_states(&state_machine);

    int32_t input = 1; // Example input
    execute_actuator(&state_machine, input);

    return 0;
}
