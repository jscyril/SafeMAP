pub fn read_or_zero(p: Option<&i32>) -> i32 {
    match p {
        Some(value) => *value,
        None => 0,
    }
}
