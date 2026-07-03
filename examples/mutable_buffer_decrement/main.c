#include <stdio.h>

void decrement_all(int *arr, int len) {
    for (int i = 0; i < len; i++) {
        arr[i] += -1;
    }
}

int main(void) {
    int values[] = {4, 5, 6};
    decrement_all(values, 3);
    printf("%d %d %d\n", values[0], values[1], values[2]);
    return 0;
}
