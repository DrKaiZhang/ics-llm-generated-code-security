/* model=qwen2.5-coder-0.5b task=T04 rep=2 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>

#define WATCHDOG_TIMEOUT 1000 // Timeout in milliseconds

// Define a struct to store consumer information
struct consumer {
    int index;
    pthread_t thread;
    void* data;
};

// Lock-free list structure
typedef struct {
    pthread_mutex_t lock;
    struct consumer* head;
} consumer_list;

// Function to check for overflow in elapsed time
static bool overflows(const uint64_t* elapsed_time) {
    return *elapsed_time > UINT64_MAX;
}

// Function to calculate elapsed time in microseconds
static uint64_t elapsed_time_microseconds(const uint64_t* elapsed_time) {
    return ((uint64_t)*elapsed_time) / 1000;
}

// Function to register a consumer
static void register_consumer(consumer_list* list, const char* name, void* data, pthread_t thread) {
    if (thread == NULL) {
        fprintf(stderr, "Failed to register consumer: Invalid thread\n");
        return;
    }

    pthread_mutex_lock(&list->lock);
    consumer* new_consumer = (consumer*)malloc(sizeof(consumer));
    if (new_consumer == NULL) {
        fprintf(stderr, "Failed to allocate memory for consumer\n");
        pthread_mutex_unlock(&list->lock);
        return;
    }

    new_consumer->index = list->head->index + 1;
    new_consumer->data = data;
    new_consumer->thread = thread;
    new_consumer->elapsed_time = NULL;

    // Initialize elapsed time
    new_consumer->elapsed_time = (uint64_t*)&elapsed_time_microseconds;
    *new_consumer->elapsed_time = 0;

    // Add to the list
    list->head = new_consumer;
    pthread_mutex_unlock(&list->lock);

    printf("Consumer registered: %s\n", name);
}

// Function to unregister a consumer
static void unregister_consumer(consumer_list* list, const char* name) {
    consumer* current = list->head;
    while (current != NULL) {
        if (strcmp(current->name, name) == 0) {
            // Found the consumer, remove it from the list
            if (current->thread != NULL) {
                pthread_join(current->thread, NULL);
            }
