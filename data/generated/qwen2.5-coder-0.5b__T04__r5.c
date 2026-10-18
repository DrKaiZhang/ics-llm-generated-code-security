/* model=qwen2.5-coder-0.5b task=T04 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <pthread.h>

typedef struct {
    uint32_t consumer_id;
    bool is_liveness_token_valid;
    uint64_t timestamp;
    bool is_active;
} WatchdogConsumer;

#define MAX_CONSUMERS 100

typedef struct {
    int8_t liveness_token_index;
    uint64_t last_consumed_timestamp;
    uint32_t token_value;
} WatchdogToken;

typedef struct {
    WatchdogConsumer consumers[MAX_CONSUMERS];
    uint32_t num_consumers;
    WatchdogToken token;
    pthread_mutex_t lock;
} WatchdogHardware;

static WatchdogHardware watchdog_hardware = {
    .consumers = {0},
    .num_consumers = 0,
    .token = {
        .liveness_token_index = -1,
        .last_consumed_timestamp = 0,
        .token_value = 0
    },
    .lock = PTHREAD_MUTEX_INITIALIZER
};

void register_consumer(WatchdogHardware* watchdog, uint32_t consumer_id) {
    if (consumer_id < 0 || consumer_id >= MAX_CONSUMERS) {
        fprintf(stderr, "Invalid consumer ID\n");
        return;
    }

    for (uint32_t i = 0; i < watchdog->num_consumers; ++i) {
        if (watchdog->consumers[i].consumer_id == consumer_id) {
            fprintf(stderr, "Consumer ID already registered\n");
            return;
        }
    }

    watchdog->consumers[watchdog->num_consumers] = (WatchdogConsumer){.
        .consumer_id = consumer_id,
        .is_liveness_token_valid = false,
        .timestamp = 0,
        .is_active = false
    };
    ++watchdog->num_consumers;
}

void reset_watchdog(WatchdogHardware* watchdog) {
    for (uint32_t i = 0; i < watchdog->num_consumers; ++i) {
        watchdog->consumers[i].is_active = false;
        watchdog->consumers[i].timestamp = 0;
        watchdog->consumers[i].is_liveness_token_valid = false;
    }
    watchdog->token.liveness_token_index = -1;
    watchdog->token.last_consumed_timestamp = 0;
    watchdog->token.token_value = 0;
}

bool is_liveness_token_valid(W
