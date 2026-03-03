#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "hash.h"

// Returns the index where the key should be stored
unsigned int HashIndex(const char* key) {
    if (key == NULL) return 0;  // NULL check
    unsigned int sum = 0;       // initialized to 0
    for (const char* c = key; *c != '\0'; c++) {  // dereference check, not pointer check
        sum += (unsigned char)*c;
    }
    return sum % MAP_MAX;  // keep within bounds
}

// Allocates memory for the HashMap
HashMap* HashInit() {
    return calloc(1, sizeof(HashMap));  // calloc zeroes memory — no garbage pointers
}

// Inserts PairValue into the map, if the value exists, increase ValueCount
void HashAdd(HashMap *map, PairValue *value) {
    if (map == NULL || value == NULL) return;  // NULL check
    unsigned int idx = HashIndex(value->KeyName);
    if (map->data[idx])
        value->Next = map->data[idx];  // was ->Next, lost existing head

    map->data[idx] = value;
}

// Returns PairValue from the map if a given key is found
PairValue* HashFind(HashMap *map, const char* key) {
    if (map == NULL || key == NULL) return NULL;  // NULL check
    unsigned int idx = HashIndex(key);

    for (PairValue* val = map->data[idx]; val != NULL; val = val->Next) {
        if (strcmp(val->KeyName, key) == 0)  // == 0 means match
            return val;
    }

    return NULL;
}

// Deletes the entry with the given key from the map
void HashDelete(HashMap *map, const char* key) {
    if (map == NULL || key == NULL) return;  // NULL check
    unsigned int idx = HashIndex(key);

    for (PairValue* val = map->data[idx], *prev = NULL; val != NULL; prev = val, val = val->Next) {
        if (strcmp(val->KeyName, key) == 0) {  // == 0 means match
            if (prev)
                prev->Next = val->Next;
            else
                map->data[idx] = val->Next;
            return;  // stop after first match
        }
    }
}

// Prints all content of the map
void HashDump(HashMap *map) {
    if (map == NULL) return;  // NULL check
    for (unsigned int i = 0; i < MAP_MAX; i++) {
        for (PairValue* val = map->data[i]; val != NULL; val = val->Next) {
            printf("%s\n", val->KeyName);  // was printf(val->KeyName) — format string vuln
        }
    }
}

int main() {
    HashMap* map = HashInit();
    if (map == NULL) {  // check allocation result
        fprintf(stderr, "HashInit() failed\n");
        return 1;
    }
    printf("%s\n", "HashInit() Successful");

    PairValue pv1 = { .KeyName = "test_key", .ValueCount = 1, .Next = NULL };
    PairValue pv2 = { .KeyName = "other_key", .ValueCount = 1, .Next = NULL };

    printf("HashAdd(map, '%s')\n", pv1.KeyName);
    HashAdd(map, &pv1);

    printf("HashAdd(map, '%s')\n", pv1.KeyName);
    HashAdd(map, &pv1);

    printf("HashAdd(map, '%s')\n", pv2.KeyName);
    HashAdd(map, &pv2);

    printf("HashFind(map, %s) = ", pv1.KeyName);
    PairValue* result = HashFind(map, pv1.KeyName);
    if (result) {
        printf("{'%s': %d}\n", result->KeyName, result->ValueCount);
    } else {
        printf("%s\n", "Not found");
    }

    printf("%s\n", "HashDump(map) =");
    HashDump(map);

    printf("HashDelete(map, '%s')\n", pv1.KeyName);
    HashDelete(map, pv1.KeyName);

    printf("HashFind(map, %s) = ", pv1.KeyName);
    result = HashFind(map, pv1.KeyName);
    if (result) {
        printf("{'%s': %d}\n", result->KeyName, result->ValueCount);
    } else {
        printf("%s\n", "Not found");
    }

    printf("%s\n", "HashDump(map) =");
    HashDump(map);

    free(map);
    return 0;
}
