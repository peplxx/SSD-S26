#include<stdio.h>
#include<stdlib.h>

void program1(int N) {
    int *arr = malloc(N*sizeof(int));
    for(int i = 0; i < N; i++) {
        arr[i] = i * i;
        printf("arr[%d] = %d\n", i, arr[i]);
    }
    free(arr);
}

int main() {
    program1(4); // Should print the array [0, 1, 4, 9]
}
