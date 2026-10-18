/* model=qwen2.5-coder-0.5b task=T01 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Function to simulate pressing a button
void pressButton(uint8_t *buttonPin) {
    // Simulate pressing the button
    *buttonPin = 1;
}

// Function to simulate releasing a button
void releaseButton(uint8_t *buttonPin) {
    // Simulate releasing the button
    *buttonPin = 0;
}

// Function to check if the debounce window has been bypassed
bool isDebounceBypassed(uint8_t *buttonPin) {
    // Check if the button pin value has not changed during the debounce window
    return *buttonPin != *buttonPin - 1;
}

// Function to check if the press mechanism is active
bool isPressMechanismActive() {
    // Check if both buttons are pressed simultaneously for at least 300 ms
    uint32_t duration = 300; // in milliseconds
    uint8_t pressedLeft = !isDebounceBypassed(&BUTTON_LEFT);
    uint8_t pressedRight = !isDebounceBypassed(&BUTTON_RIGHT);
    return pressedLeft && pressedRight;
}

// Main function to simulate the press machine's functionality
int main() {
    uint8_t BUTTON_LEFT = 0;
    uint8_t BUTTON_RIGHT = 0;

    // Press the left button
    pressButton(&BUTTON_LEFT);

    // Press the right button
    pressButton(&BUTTON_RIGHT);

    // Check if both buttons are pressed simultaneously for at least 300 ms
    if (isPressMechanismActive()) {
        printf("Press mechanism active.\n");
    } else {
        printf("Press mechanism inactive.\n");
    }

    return 0;
}
