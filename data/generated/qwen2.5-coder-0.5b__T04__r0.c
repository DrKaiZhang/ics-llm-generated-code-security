/* model=qwen2.5-coder-0.5b task=T04 rep=0 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#define MAX_CONSUMERS 100
#define TOKEN_SIZE 16
#define OVERFLOW_THRESHOLD 10000

typedef struct {
    uint32_t timestamp;
    bool refreshed;
} WatchdogToken;

typedef struct {
    WatchdogToken tokens[MAX_CONSUMERS];
    size_t token_count;
    size_t last_refreshed_index;
    int8_t overflow;
} WatchdogManager;

void watchdog_register(WatchdogManager *manager, const char *token) {
    if (manager->token_count == MAX_CONSUMERS) {
        return;
    }

    for (size_t i = 0; i < manager->token_count; i++) {
        if (strcmp(tokens[i].token, token) == 0) {
            return;
        }
    }

    tokens[manager->token_count].timestamp = (uint32_t)time(NULL);
    tokens[manager->token_count].refreshed = true;
    manager->token_count++;
}

bool watchdog_update(WatchdogManager *manager) {
    for (size_t i = 0; i < manager->token_count; i++) {
        if (!tokens[i].refreshed) {
            continue;
        }

        uint32_t timestamp = tokens[i].timestamp;
        uint32_t elapsed_time = (uint32_t)(timestamp - (uint32_t)time(NULL));

        // Overflows check
        if (elapsed_time > OVERFLOW_THRESHOLD) {
            manager->overflow++;
        }

        // Check for duplicates
        if (manager->last_refreshed_index != -1 && strcmp(tokens[i].token, manager->tokens[manager->last_refreshed_index].token) == 0) {
            return false;
        }

        // Update the last refreshed index
        manager->last_refreshed_index = i;
    }

    return true;
}
