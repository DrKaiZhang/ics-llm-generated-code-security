/* model=qwen2.5-coder-0.5b task=T04 rep=1 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <sys/time.h>
#include <pthread.h>

// Define the watchdog structure
struct Watchdog {
    struct timespec lastRefreshed;
    pthread_mutex_t lock;
};

// Function to initialize the watchdog
void watchdog_init(struct Watchdog *watchdog) {
    pthread_mutex_init(&watchdog->lock, NULL);
}

// Function to register a consumer
void watchdog_register(struct Watchdog *watchdog, uint32_t index) {
    // Check for duplicates and invalid indices
    if (index >= watchdog->lastRefreshed.tv_sec || index < 0 || watchdog->lastRefreshed.tv_nsec == 0) {
        return;
    }

    // Lock the watchdog
    pthread_mutex_lock(&watchdog->lock);

    // Add to the list of consumers
    // Note: This part should be implemented based on the actual storage mechanism
    // For simplicity, let's assume a linked list
    // Note: In practice, you would need to allocate space for the list
    // Note: You should also ensure that each element is unique and sorted

    // Unlock the watchdog
    pthread_mutex_unlock(&watchdog->lock);
}

// Function to unregister a consumer
void watchdog_unregister(struct Watchdog *watchdog, uint32_t index) {
    // Check for duplicates and invalid indices
    if (index >= watchdog->lastRefreshed.tv_sec || index < 0 || watchdog->lastRefreshed.tv_nsec == 0) {
        return;
    }

    // Lock the watchdog
    pthread_mutex_lock(&watchdog->lock);

    // Remove from the list of consumers
    // Note: This part should be implemented based on the actual storage mechanism
    // Note: You should also ensure that each element is unique and sorted

    // Unlock the watchdog
    pthread_mutex_unlock(&watchdog->lock);
}

// Function to check the last refresh time
bool watchdog_check_refreshed(struct Watchdog *watchdog) {
    // Lock the watchdog
    pthread_mutex_lock(&watchdog->lock);

    // Check if the last refresh was more than 1 second ago
    if (time(NULL) - watchdog->lastRefreshed.tv_sec > 1) {
        watchdog->lastRefreshed = time(NULL);
        return true;
    }

    // Unlock the watchdog
    pthread_mutex_unlock(&watchdog->lock);
    return false;
}
``
