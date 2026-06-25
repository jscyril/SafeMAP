pub fn divide(a: i32, b: i32) -> Result<i32, i32> {
    if b == 0 {
        Err(-1)
    } else {
        Ok(a / b)
    }
}

