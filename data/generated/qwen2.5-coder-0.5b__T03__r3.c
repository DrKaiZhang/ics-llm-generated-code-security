/* model=qwen2.5-coder-0.5b task=T03 rep=3 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Define constants
#define PI 3.14159265358979323846
#define Kp 10.0f
#define Ki 0.0f
#define Kd 0.0f
#define Min_Q15 0x80000000
#define Max_Q15 0xFFFF0000

// Function prototypes
void PIDController_Init(float* Q);
float PIDController_Update(float* Q, float current, float desired, float dt);

int main() {
    float Q15 = 1.0f; // Example Q15 value
    PIDController_Init(&Q15);
    return 0;
}

void PIDController_Init(float* Q) {
    *Q = 1.0f;
    Ki = 0.0f; // Default Ki
    Kd = 0.0f; // Default Kd
    Min_Q15 = 0x80000000; // Set minimum Q15 to protect against overflow
    Max_Q15 = 0xFFFF0000; // Set maximum Q15 to protect against overflow
}

float PIDController_Update(float* Q, float current, float desired, float dt) {
    if (*Q <= Min_Q15 || *Q >= Max_Q15) {
        *Q = Min_Q15; // Clamp Q value
    }

    float error = desired - current;

    float P = error * Kp;
    float I = integralSum(Q) * Ki;
    float D = (error - lastError) / dt * Kd;

    float nextError = error + P + I + D;

    // Update Q value using the PID formula
    *Q = Q + (nextError - error) * dt;

    // Update lastError for next iteration
    lastError = nextError;

    return *Q;
}

float integralSum(float* Q) {
    int sum = 0;
    for (int i = 0; i < 4; ++i) {
        sum += *(Q + i);
    }
    return sum;
}
