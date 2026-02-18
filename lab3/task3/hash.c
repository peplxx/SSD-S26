#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "hash.h"

// Returns the index where the key should be stored
int HashIndex(char* key) {
    int sum;
    for (char* c = key; c; c++) {
        sum += *c;
    }
    return sum;
}

// Allocates memory for the HashMap
HashMap* HashInit() {
    return malloc(sizeof(HashMap));
}

// Inserts PairValue into the map, if the value exists, increase ValueCount
void HashAdd(HashMap *map, PairValue *value) {
    int idx = HashIndex(value->KeyName);
    if (map->data[idx]) 
        value->Next = map->data[idx]->Next;

    map->data[idx] = value;	
}

// Returns PairValue from the map if a given key is found
PairValue* HashFind(HashMap *map, const char* key) {
    unsigned idx = HashIndex(key);
    
    for(PairValue* val = map->data[idx]; val != NULL; val = val->Next) {
        if (strcmp(val->KeyName, key))
            return val;
    }
    
    return NULL; 
}

// Deletes the entry with the given key from the map
void HashDelete(HashMap *map, const char* key) {
    unsigned idx = HashIndex(key);

    for(PairValue* val = map->data[idx], *prev = NULL; val != NULL; prev = val, val = val->Next) {
        if (strcmp(val->KeyName, key)) {
            if (prev)
                prev->Next = val->Next;
            else
                map->data[idx] = val->Next;
        }
    }
}

// Prints all content of the map
void HashDump(HashMap *map) {
    for(unsigned i = 0; i < MAP_MAX; i++) {
        for(PairValue* val = map->data[i]; val != NULL; val = val->Next) {
            printf(val->KeyName);
        }
    }
}

int main() {
    HashMap* map = HashInit();
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
    if(result) {
        printf("{'%s': %d}\n", result->KeyName, result->ValueCount);
    }
    else {
        printf("%s\n", "Not found");
    }
    
    printf("%s", "HashDump(map) = ");
    HashDump(map);

    printf("HashDelete(map, '%s')\n", pv1.KeyName);
    HashDelete(map, pv1.KeyName);

    printf("HashFind(map, %s) = ", pv1.KeyName);
    result = HashFind(map, pv1.KeyName); 
    if(result) {
        printf("{'%s': %d}\n", result->KeyName, result->ValueCount);
    }
    else {
        printf("%s\n", "Not found");
    }

    printf("%s", "HashDump(map) = ");
    HashDump(map);

    free(map);
}
