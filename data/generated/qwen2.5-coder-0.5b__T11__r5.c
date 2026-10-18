/* model=qwen2.5-coder-0.5b task=T11 rep=5 seed=20260101 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

typedef struct {
    uint8_t sof;
    uint16_t length;
    uint8_t payload[0];
    uint8_t crc;
    uint8_t eof;
    bool state;
    size_t read_position;
} IndustrialSerialParser;

void IndustrialSerialParser_init(IndustrialSerialParser *parser) {
    parser->sof = 0;
    parser->length = 0;
    parser->payload[0] = 0;
    parser->crc = 0;
    parser->eof = 0;
    parser->state = false;
    parser->read_position = 0;
}

bool IndustrialSerialParser_is_valid_length(const IndustrialSerialParser *parser, uint16_t length) {
    return length > 0 && length <= parser->max_length;
}

void IndustrialSerialParser_process_data(IndustrialSerialParser *parser, uint8_t data) {
    if (parser->state == false) {
        parser->sof = data;
        parser->state = true;
        return;
    }

    if (parser->state == true) {
        parser->length += 1;
        if (parser->length > parser->max_length) {
            parser->state = false;
        }
        if (parser->state == true && parser->eof) {
            parser->state = false;
            parser->read_position = 0;
        }
        if (parser->state == true && parser->length != parser->max_length) {
            uint8_t copy_count = parser->length - parser->max_length;
            memcpy(parser->payload, &data, copy_count);
            parser->read_position += copy_count;
        }
        if (parser->state == true && parser->length == parser->max_length) {
            uint8_t checksum = 0;
            for (size_t i = 0; i < parser->length; ++i) {
                checksum += parser->payload[i];
            }
            if (checksum != parser->crc) {
                parser->state = false;
                return;
            }
            parser->read_position = 0;
        }
    }
}
