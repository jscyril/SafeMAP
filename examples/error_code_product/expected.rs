pub fn multiply_checked(a: i32, b: i32) -> Result<i32, i32> {
    if b == 0 {
        return Err(-2);
    }
    Ok(a * b)
}
