struct Pair {
    int left;
    int right;
};

int sum4(const int values[4]) {
    int sum = 0;
    for (int i = 0; i < 4; ++i) {
        sum += values[i];
    }
    return sum;
}

int pair_total(const struct Pair *pair) {
    return pair->left + pair->right;
}

int square(int value) {
    return value * value;
}

int composed(int value) {
    return square(value) + 1;
}

int main(void) {
    return composed(2);
}
