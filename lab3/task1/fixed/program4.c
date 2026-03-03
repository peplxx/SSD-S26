#include<stdio.h>
#include<stdlib.h>
#include<string.h>

char* getString() {
    char message[100] = "Hello World!";
    char* ret = (char*)malloc(100*sizeof(char));
    strcpy(ret, message);
    return ret;
}

void program4() {
    char * string = getString();
    printf("String: %s\n", string);
    free(string);
}

int main() {
    program4();
}
