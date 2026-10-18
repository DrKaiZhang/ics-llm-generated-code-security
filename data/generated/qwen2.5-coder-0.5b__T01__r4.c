/* model=qwen2.5-coder-0.5b task=T01 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

typedef uint8_t ButtonState;

ButtonState Interlock2HandSafety(int leftButton, int rightButton) {
    uint8_t lastLeftState = 0;
    uint8_t lastRightState = 0;
    uint8_t debounceCount = 0;

    while (1) {
        if (lastLeftState == 0 && lastRightState == 0) {
            // Reset debounce counter
            debounceCount = 0;
        }

        // Get current state of left button
        uint8_t leftState = (leftButton & 1);
        if (leftState == 0) {
            lastLeftState = 1;
        }

        // Get current state of right button
        uint8_t rightState = (rightButton & 1);
        if (rightState == 0) {
            lastRightState = 1;
        }

        // Check debounce count
        if (debounceCount >= 300) {
            // Disengage machine output immediately
            return false;
        }

        // Update debounce count
        debounceCount++;

        // Wait for button release
        while (leftButton & 1 || rightButton & 1) {
            if ((leftButton & 1) && !leftButton) {
                // Left button released
                break;
            }
            if ((rightButton & 1) && !rightButton) {
                // Right button released
                break;
            }
            // Wait until button becomes non-pressed
            while (!(leftButton & 1) || !(rightButton & 1)) {
                // Wait until button is pressed again
            }
        }
    }

    // Machine output is enabled
    return true;
}
