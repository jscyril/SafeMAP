#include <stdio.h>

int total_array(const int *arr, int len) {
    int total = 0;
    for (int i = 0; i < len; i++) total += arr[i];
    return total;
}

int main(void) {
    int values[] = {2, 4, 6};
    printf("%d\n", total_array(values, 3));
    return 0;
}
