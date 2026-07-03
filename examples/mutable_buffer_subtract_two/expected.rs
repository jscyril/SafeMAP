pub fn subtract_two_all(arr: &mut [i32]) {
    for value in arr.iter_mut() {
        *value += -2;
    }
}
