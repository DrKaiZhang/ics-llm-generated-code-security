/* model=qwen2.5-coder-0.5b task=T03 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// Define the PID controller structure
typedef struct {
    int Kp;
    int Ki;
    int Kd;
    int min;
    int max;
    double input;
    double output;
    double accumulatedInput;
    double accumulatedError;
} PIDController;

// Function to initialize the PID controller
void PIDController_init(PIDController *controller, int Kp, int Ki, int Kd, int min, int max) {
    controller->Kp = Kp;
    controller->Ki = Ki;
    controller->Kd = Kd;
    controller->min = min;
    controller->max = max;
    controller->accumulatedInput = 0;
    controller->accumulatedError = 0;
}

// Function to calculate the output of the PID controller
double PIDController_output(PIDController *controller, double currentInput) {
    if (currentInput == 0) {
        return controller->output; // Return output if current input is zero
    }

    // Calculate the error between currentInput and desiredOutput
    double error = currentInput - controller->output;

    // Calculate the derivative of the error
    double derivative = error - controller->accumulatedError;

    // Calculate the integral term
    double integral = controller->accumulatedInput * controller->Kd;

    // Accumulate the errors
    controller->accumulatedError += error;

    // Compute the new output
    controller->output = controller->input + controller->Kp * error + controller->Ki * integral + controller->Kd * derivative;

    // Apply bounds
    if (controller->output < controller->min) {
        controller->output = controller->min;
    } else if (controller->output > controller->max) {
        controller->output = controller->max;
    }

    return controller->output;
}

int main() {
    PIDController controller = {0, 0, 0, 0, 10, 20}; // Default tuning parameters

    // Example usage
    double currentInput = 30;
    double output = PIDController_output(&controller, currentInput);

    printf("Current Input: %f\n", currentInput);
    printf("PID Output: %f\n", output);

    return 0;
}
