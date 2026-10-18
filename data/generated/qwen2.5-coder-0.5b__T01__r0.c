/* model=qwen2.5-coder-0.5b task=T01 rep=0 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define DEBOUNCE_WINDOW_MS 300

// Function to toggle the machine's output based on two push buttons
bool toggleMachineOutput(uint8_t leftButtonPressed, uint8_t rightButtonPressed) {
    uint16_t lastDebounceCount = 0;

    // Function to check if a button has been pressed
    bool buttonPressed = false;

    // Debounce logic
    while (!buttonPressed && lastDebounceCount < DEBOUNCE_WINDOW_MS) {
        if (!leftButtonPressed) {
            leftButtonPressed = true;
        }
        if (!rightButtonPressed) {
            rightButtonPressed = true;
        }
        lastDebounceCount++;

        if (lastDebounceCount >= DEBOUNCE_WINDOW_MS) {
            buttonPressed = true;
        }
    }

    // If both buttons were pressed at least 300 ms ago, turn off the output
    return buttonPressed;
}

int main() {
    // Example usage
    bool output = toggleMachineOutput(true, true);
    if (output) {
        printf("Machine output is enabled.\n");
    } else {
        printf("Machine output is disabled.\n");
    }
    return 0;
}
