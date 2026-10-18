/* model=qwen2.5-coder-0.5b task=T07 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define NUM_STEPS 5

enum State {
    IDLE,
    READY,
    MOVING,
    Dwell,
    RETURNING,
    FAULT
};

typedef struct StateTransition {
    uint8_t next_state;
    uint8_t step_index;
    double delay;
} StateTransition;

StateTransition transitions[NUM_STEPS] = {
    {READY, 0, 0.1}, // Move to ready after 100ms
    {MOVING, 1, 0.2}, // Move to moving after 200ms
    {Dwell, 2, 0.3}, // Move to dwell after 300ms
    {RETURNING, 3, 0.4}, // Move to returning after 400ms
    {FAULT, 4, 0.5}, // Fault after 500ms
};

int main() {
    uint8_t currentState = IDLE;
    double currentTime = 0.0;
    bool emergencyStop = false;

    while (!emergencyStop) {
        currentState = getNextState(currentState, currentTime);
        currentTime += transitions[currentState].delay;
        if (currentTime > 1.0) {
            emergencyStop = true;
        }
    }

    return 0;
}

uint8_t getNextState(uint8_t currentState, double currentTime) {
    switch (currentState) {
        case IDLE:
            if (currentTime < 0.5) {
                return READY;
            } else {
                return FAULT;
            }
        case READY:
            if (currentTime < 0.25) {
                return MOVING;
            } else {
                return Dwell;
            }
        case MOVING:
            if (currentTime < 0.15) {
                return RETURNING;
            } else {
                return FAULT;
            }
        case Dwell:
            if (currentTime < 0.05) {
                return FAULT;
            } else {
                return FAULT;
            }
        case RETURNING:
            if (currentTime < 0.025) {
                return FAULT;
            } else {
                return FAULT;
            }
        default:
            return FAULT;
    }
}
