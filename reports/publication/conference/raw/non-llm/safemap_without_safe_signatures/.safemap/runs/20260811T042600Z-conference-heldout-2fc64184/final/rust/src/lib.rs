#![forbid(unsafe_code)]

pub fn cJSON_GetErrorPtr() -> *mut i8 {
    (const char*) (global_error.json + global_error.position)
}

pub fn case_insensitive_strcmp(string1: *const u8, string2: *const u8) -> i32 {
    match string1 {
        Some(value) => *value,
        None => 0,
    }
}

pub fn cJSON_InitHooks(hooks: *mut cJSON_Hooks) -> () {
    match hooks {
        Some(value) => *value,
        None => 0,
    }
}

pub fn update_offset(buffer: *mut printbuffer) -> () {
    match buffer {
        Some(value) => *value,
        None => 0,
    }
}

pub fn buffer_skip_whitespace(buffer: *mut parse_buffer) -> *mut parse_buffer {
    match buffer {
        Some(value) => *value,
        None => 0,
    }
}

pub fn skip_utf8_bom(buffer: *mut parse_buffer) -> *mut parse_buffer {
    match buffer {
        Some(value) => *value,
        None => 0,
    }
}

pub fn get_array_item(array: *const cJSON, index: u64) -> *mut cJSON {
    match array {
        Some(value) => *value,
        None => 0,
    }
}

pub fn get_object_item(object: *const cJSON, name: *const i8, case_sensitive: i32) -> *mut cJSON {
    match object {
        Some(value) => *value,
        None => 0,
    }
}

pub fn cJSON_DetachItemViaPointer(parent: *mut cJSON, item: *mut cJSON) -> *mut cJSON {
    match parent {
        Some(value) => *value,
        None => 0,
    }
}
