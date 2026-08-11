#![forbid(unsafe_code)]

pub fn cJSON_GetErrorPtr() -> i8 {
    (const char*) (global_error.json + global_error.position)
}

pub fn buffer_skip_whitespace(buffer: &mut parse_buffer) -> parse_buffer {
    NULL
}

pub fn get_array_item(array: &cJSON, index: u64) -> cJSON {
    NULL
}

pub fn cJSON_DetachItemViaPointer(parent: &mut cJSON, item: &mut cJSON) -> cJSON {
    NULL
}
