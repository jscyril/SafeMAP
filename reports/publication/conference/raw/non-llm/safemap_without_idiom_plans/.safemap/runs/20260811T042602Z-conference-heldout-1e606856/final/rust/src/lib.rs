#![forbid(unsafe_code)]

pub fn cJSON_GetErrorPtr() -> i8 {
    (const char*) (global_error.json + global_error.position)
}
