/* model=qwen2.5-coder-0.5b task=T11 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Define the maximum length of a frame
#define MAX_FRAME_LENGTH 1024

typedef struct {
    uint8_t sof;
    uint16_t length;
    uint8_t payload[MAX_FRAME_LENGTH];
    uint16_t crc;
    bool end_of_frame;
} Frame;

// Function to parse the frame
bool parse_frame(Frame *frame) {
    // Check if the SOF is valid
    if (!frame->sof || frame->length > MAX_FRAME_LENGTH) {
        return false;
    }
    
    // Check if the end of frame has been reached
    if (frame->end_of_frame) {
        return true;
    }
    
    // Read the payload into the frame
    for (size_t i = 0; i < frame->length; ++i) {
        frame->payload[i] = uart_getc();
    }
    
    // Calculate the CRC
    frame->crc = 0xFFFF;
    for (size_t i = 0; i < frame->length; ++i) {
        frame->crc ^= frame->payload[i];
    }
    
    // Check if the CRC matches the expected value
    if (frame->crc != 0) {
        return false;
    }
    
    // Set the end of frame flag
    frame->end_of_frame = true;
    
    // Return true if the frame is parsed successfully
    return true;
}

// Main function
int main() {
    Frame frame;
    bool result = parse_frame(&frame);
    if (result) {
        printf("Frame parsed successfully!\n");
    } else {
        printf("Error parsing frame: %s\n", frame.error_message);
    }
    
    return 0;
}
