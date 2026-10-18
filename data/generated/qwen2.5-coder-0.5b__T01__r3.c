/* model=qwen2.5-coder-0.5b task=T01 rep=3 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Function to simulate pressing two buttons (left, right) simultaneously
// and return true if the button is pressed within 300 ms, otherwise false.
bool isButtonPressed(const bool leftPressed, const bool rightPressed) {
    // Simulate debouncing by checking the transition count
    int debounceCount = 0;
    while (debounceCount < 300) {
        if (!leftPressed && !rightPressed) {
            return false;
        }
        leftPressed = !leftPressed;
        rightPressed = !rightPressed;
        debounceCount++;
    }
    return true;
}

// Example usage:
bool isMachineEnabled() {
    return isButtonPressed(true, true); // Simulate pressing both buttons simultaneously
}
