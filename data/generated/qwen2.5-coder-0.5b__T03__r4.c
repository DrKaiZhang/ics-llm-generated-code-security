/* model=qwen2.5-coder-0.5b task=T03 rep=4 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define PI 3.141592653589793
#define MAX_P 0x7FFF
#define MIN_P 0xFF
#define MAX_I 0x7FFF
#define MIN_I 0xFF
#define MAX_D 0x7FFF
#define MIN_D 0xFF
#define SAFE_MIN 10
#define SAFE_MAX 100

struct pid_t {
    uint16_t p;
    uint16_t i;
    uint16_t d;
    uint16_t min_p;
    uint16_t max_p;
    uint16_t min_i;
    uint16_t max_i;
    uint16_t min_d;
    uint16_t max_d;
    uint16_t prev_error;
};

// Initialize PID controller with default settings
void pid_init(struct pid_t *pid) {
    pid->p = MIN_P;
    pid->i = MIN_I;
    pid->d = MIN_D;
    pid->min_p = MIN_P;
    pid->max_p = MAX_P;
    pid->min_i = MIN_I;
    pid->max_i = MAX_I;
    pid->min_d = MIN_D;
    pid->max_d = MAX_D;
    pid->prev_error = 0;
}

// Update PID controller with new error
void pid_update(struct pid_t *pid, uint16_t error) {
    uint16_t derivative = error - pid->prev_error;
    pid->prev_error = error;

    // Clamp integral to prevent windup
    if (pid->i > pid->max_i) {
        pid->i = pid->max_i;
    }

    // Clamp derivative to prevent overflow
    if (derivative > pid->max_d) {
        derivative = pid->max_d;
    }

    // Calculate new integral term
    pid->i += derivative / PI;

    // Calculate new derivative term
    pid->d = (error - pid->prev_error) / PI;

    // Output saturation
    if (pid->i > pid->max_i) {
        pid->i = pid->max_i;
    }
    if (pid->d > pid->max_d) {
        pid->d = pid->max_d;
    }
