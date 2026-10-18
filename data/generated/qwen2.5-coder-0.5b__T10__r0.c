/* model=qwen2.5-coder-0.5b task=T10 rep=0 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

enum AlarmCode {
    ALARM_CODE_HIGH,
    ALARM_CODE_LOW,
    ALARM_CODE_ERROR
};

int process_alarm_eval(float process_variable, float low_limit, float high_limit, uint8_t rate_of_change) {
    if (process_variable > high_limit) {
        // High limit exceeded, trigger alarm
        return ALARM_CODE_HIGH;
    } else if (process_variable < low_limit) {
        // Low limit exceeded, clear alarm
        return ALARM_CODE_LOW;
    }
    
    // Calculate change since last check
    float change = process_variable - low_limit;
    
    // Check if hysteresis is enabled
    if (rate_of_change > 0) {
        // Enable hysteresis
        change += rate_of_change * 0.5; // Adjust rate of change for hysteresis
    }
    
    // Clamp change to prevent overflow
    change = (change > high_limit ? high_limit : change);
    change = (change < low_limit ? low_limit : change);
    
    // Check if change meets threshold
    if (change > high_limit - low_limit) {
        // Threshold met, clear alarm
        return ALARM_CODE_LOW;
    }
    
    return ALARM_CODE_OK;
}

int main() {
    float process_value = 34.5;
    float low_limit = 10.0;
    float high_limit = 20.0;
    uint8_t rate_of_change = 10.0;
    
    int result = process_alarm_eval(process_value, low_limit, high_limit, rate_of_change);
    printf("Alarm state: %d\n", result);

    return 0;
}
