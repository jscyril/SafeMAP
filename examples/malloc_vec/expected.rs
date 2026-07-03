pub fn make_sequence(len: i32) -> Vec<i32> {
    let len = len.max(0) as usize;
    (0..len).map(|value| value as i32).collect()
}
