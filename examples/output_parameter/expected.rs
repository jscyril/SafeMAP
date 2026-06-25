pub fn get_max(arr: &[i32]) -> Result<i32, i32> {
    arr.iter().copied().max().ok_or(-1)
}

