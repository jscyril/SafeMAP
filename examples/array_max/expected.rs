pub fn array_max(arr: &[i32]) -> i32 {
    arr.iter().copied().max().unwrap()
}
