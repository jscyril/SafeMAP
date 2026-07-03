#include <stdio.h>

void increment_all(int *arr, int len) {
    for (int i = 0; i < len; i++) {
        arr[i] += 1;
    }
}

int main(void) {
    int values[] = {1, 2, 3};
    increment_all(values, 3);
    printf("%d %d %d\n", values[0], values[1], values[2]);
    return 0;
}
