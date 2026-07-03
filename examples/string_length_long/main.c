#include <stdio.h>
#include <string.h>

long string_length_long(const char *text) {
    return strlen(text);
}

int main(void) {
    printf("%ld\n", string_length_long("hello"));
    return 0;
}
