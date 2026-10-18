/* model=qwen2.5-coder-0.5b task=T01 rep=1 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

bool pressMachineSafetyInterlock(uint8_t leftButtonState, uint8_t rightButtonState) {
    // Check if both buttons are held together for at least 300 ms
    if (leftButtonState == 1 && rightButtonState == 1) {
        // Initialize debounce counter
        unsigned char debounceCount = 0;
        
        // Read input states
        bool leftInput = !(leftButtonState & 1);
        bool rightInput = !(rightButtonState & 1);
        
        // Check debounce window
        while (debounceCount < 300 && !(leftInput && rightInput)) {
            // Wait for debounce window
            for (unsigned char i = 0; i < 300; ++i) {
                // Delay for 1 ms
                usleep(1000);
            }
            
            // Read new input states
            leftInput = !(leftButtonState & 1);
            rightInput = !(rightButtonState & 1);
        }
        
        // Check if both buttons are held together after debounce window
        return leftInput && rightInput;
    }
    
    // If either button is released, output must be disengaged immediately
    return true;
}
