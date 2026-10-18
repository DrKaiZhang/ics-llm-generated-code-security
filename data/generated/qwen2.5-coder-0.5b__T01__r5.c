/* model=qwen2.5-coder-0.5b task=T01 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Define the debounce window
#define DEBOUNCE_WINDOW_MS 300

// Array to hold the states of the buttons (1 for pressed, 0 for released)
int buttons[2] = {0, 0};

// Function to handle debouncing
void debounce(uint8_t* state, int idx) {
    uint8_t current_state = state[idx];
    uint8_t previous_state = state[idx - 1];
    
    if (previous_state == 0 && current_state == 1) {
        state[idx] = 1;
    } else if (previous_state == 1 && current_state == 0) {
        state[idx] = 0;
    } else if (previous_state == 0 && current_state == 0) {
        // Reset the debounce after a long period of inactivity
        state[idx] = 0;
    }
}

// Function to handle the safety interlock
bool press_machine(int press_left, int press_right) {
    int left_stuck = 0;
    int right_stuck = 0;
    
    // Debounce the left button
    debounce(buttons, 0);
    if (buttons[0] == 1) {
        left_stuck = 1;
    }
    
    // Debounce the right button
    debounce(buttons, 1);
    if (buttons[1] == 1) {
        right_stuck = 1;
    }
    
    // Check if both buttons are pressed
    if (left_stuck + right_stuck > DEBOUNCE_WINDOW_MS) {
        return true;
    }
    
    // If either button is released, reset the debounce
    if (left_stuck == 1 || right_stuck == 1) {
        buttons[0] = 0;
        buttons[1] = 0;
        return false;
    }
    
    // If neither button is released, the machine outputs disabled
    return false;
}
