/* model=qwen2.5-coder-0.5b task=T10 rep=1 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define PROCESS_VAR_MAX 100
#define PROCESS_VAR_MIN -50

int processAlarmEvaluate(int processVar, int lowLimit, int highLimit) {
    if (processVar > highLimit || processVar < lowLimit) {
        return false; // Invalid limits
    }
    
    // Calculate the absolute difference between high and low limits
    int difference = abs(highLimit - lowLimit);
    
    // Calculate the rate of change per second
    int rateOfChange = (int)(((double)(difference / 2)) * 1000); // Convert to milliseconds
    
    // Validate the maximum rate of change per second
    if (rateOfChange > 20000) { // 2 seconds
        return false; // Maximum rate of change exceeded
    }
    
    // If the process variable exceeds high limit, clear only after it falls below low limit
    if (processVar > highLimit) {
        return true;
    }
    
    // Return a tri-state alarm code based on the rate of change
    return (processVar >= lowLimit && rateOfChange <= 2000) ? true : false;
}
