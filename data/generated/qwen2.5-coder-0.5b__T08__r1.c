/* model=qwen2.5-coder-0.5b task=T08 rep=1 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Function prototype to debounce a limit switch using a fixed-size buffer
void debounceLimitSwitch(uint8_t *sampleHistory, size_t bufferSize, bool *contactChange);

int main() {
    // Example usage
    uint8_t sample1 = 0x50;
    uint8_t sample2 = 0x60;
    uint8_t sample3 = 0x70;

    uint8_t sampleHistory[100];
    bool contactChange = false;

    debounceLimitSwitch(sampleHistory, sizeof(sampleHistory), &contactChange);

    if (contactChange) {
        printf("Contact chatter detected!\n");
    }

    return 0;
}
