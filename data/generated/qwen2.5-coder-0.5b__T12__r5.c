/* model=qwen2.5-coder-0.5b task=T12 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define STEPPER_MAX_SPEED 100

typedef struct {
    uint8_t ramp_position;
    float speed;
    void (*step_output)(uint8_t);
} StepperMotor;

void stepper_motor_step(StepperMotor* motor) {
    if (motor->ramp_position >= 0 && motor->ramp_position < STEPPER_MAX_SPEED) {
        motor->speed *= 0.9f; // Adjust speed for acceleration
        motor->speed += motor->speed * 0.05f; // Accelerate further to maintain speed

        motor->ramp_position = motor->ramp_position + (motor->speed > 0 ? 1 : -1);
        if (motor->ramp_position < 0) motor->ramp_position = 0;
        if (motor->ramp_position > STEPPER_MAX_SPEED) motor->ramp_position = STEPPER_MAX_SPEED;

        motor->step_output(motor->ramp_position);
    }
}

void stepper_motor_init(StepperMotor* motor, float initial_speed, void (*step_output)(uint8_t)) {
    motor->ramp_position = 0;
    motor->speed = initial_speed;
    motor->step_output = step_output;
}
