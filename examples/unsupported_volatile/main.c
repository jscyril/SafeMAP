#include <stdio.h>

int read_volatile(const volatile int *port) {
    volatile int value = *port;
    return value;
}

int main(void) {
    volatile int port = 9;
    printf("%d\n", read_volatile(&port));
    return 0;
}
