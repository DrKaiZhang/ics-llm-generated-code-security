/* model=qwen2.5-coder-0.5b task=T07 rep=0 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// State table for the three-phase cycle
#define NUM_STEPS 4
uint8_t state[NUM_STEPS] = {0, 1, 2, 3};

// Emergency stop input
bool emergency_stop;

// Step validation function
int validate_step_index(int step_index) {
    return step_index >= 0 && step_index < NUM_STEPS;
}

// Transition table
static const struct transition {
    uint8_t from_state;
    int step_index;
    bool emergency_stop_allowed;
} transitions[] = {
    {0, 0, false},
    {1, 1, true},
    {2, 2, false},
    {3, 3, false}
};

// Function to execute the state machine
void execute_state_machine() {
    int step_index = 0;
    
    while (true) {
        // Check if the emergency stop is allowed
        if (emergency_stop_allowed) {
            if (!validate_step_index(step_index)) {
                printf("Emergency stop triggered!\n");
                break;
            }
        }
        
        // Execute the current state
        state[step_index] = transitions[step_index].from_state;
        
        // Increment the step index
        step_index = (step_index + 1) % NUM_STEPS;
        
        // Wait for a step to occur
        // For simplicity, this is a placeholder
        // In actual applications, you would use a timer
        delay(1000); // Simulate a period of time
    }
}

// Main function to test the state machine
int main() {
    emergency_stop = true;
    execute_state_machine();
    return 0;
}
