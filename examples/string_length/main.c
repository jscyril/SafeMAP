#include <stdio.h>
#include <string.h>

int string_length(const char *text) {
    return strlen(text);
}

int main(void) {
    printf("%d\n", string_length("hello"));
    return 0;
}
