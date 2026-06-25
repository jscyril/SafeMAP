pub fn read_value(value: Option<&i32>) -> Result<i32, i32> {
    value.copied().ok_or(-1)
}

