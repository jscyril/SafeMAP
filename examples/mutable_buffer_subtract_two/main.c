#include <stdio.h>

void subtract_two_all(int *arr, int len) {
    for (int i = 0; i < len; i++) {
        arr[i] += -2;
    }
}

int main(void) {
    int values[] = {4, 5, 6};
    subtract_two_all(values, 3);
    printf("%d %d %d\n", values[0], values[1], values[2]);
    return 0;
}
