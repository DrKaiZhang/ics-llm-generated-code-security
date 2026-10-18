/* model=qwen2.5-coder-0.5b task=T04 rep=3 seed=20260101 */
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <pthread.h>

#define TOKEN_SIZE 32

struct Watchdog {
    uint8_t token[TOKEN_SIZE];
    uint64_t last_refresh;
    int consumer_count;
    pthread_mutex_t mutex;
};

void init_watchdog(struct Watchdog *watchdog) {
    memset(watchdog->token, 0, sizeof(watchdog->token));
    watchdog->last_refresh = 0;
    watchdog->consumer_count = 0;
    pthread_mutex_init(&watchdog->mutex, NULL);
}

bool register_consumer(struct Watchdog *watchdog, int index) {
    if (index >= watchdog->consumer_count || index < 0) {
        return false;
    }
    watchdog->consumer_count++;
    pthread_mutex_lock(&watchdog->mutex);
    // Update the last refresh time with the current time
    watchdog->last_refresh = clock_gettime(CLOCK_REALTIME, NULL);
    pthread_mutex_unlock(&watchdog->mutex);
    return true;
}

void refresh_watchdog(struct Watchdog *watchdog) {
    struct timespec now;
    clock_gettime(CLOCK_REALTIME, &now);

    pthread_mutex_lock(&watchdog->mutex);
    for (int i = 0; i < watchdog->consumer_count; i++) {
        uint64_t timestamp = now.tv_sec + now.tv_nsec / 10000000;
        if (timestamp > watchdog->token[i]) {
            watchdog->token[i] = timestamp;
            // Check if all consumers have received the token
            if (watchdog->consumer_count == 0) {
                // Reset the watchdog
                watchdog->last_refresh = 0;
                watchdog->consumer_count = 0;
            }
            break;
        }
    }
    pthread_mutex_unlock(&watchdog->mutex);
}

void cleanup_watchdog(struct Watchdog *watchdog) {
    pthread_mutex_destroy(&watchdog->mutex);
}
