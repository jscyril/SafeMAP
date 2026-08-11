#![forbid(unsafe_code)]

pub fn cJSON_GetErrorPtr() -> i8 {
    (const char*) (global_error.json + global_error.position)
}

pub fn case_insensitive_strcmp(string1: Option<&u8>, string2: Option<&u8>) -> i32 {
    match string1 {
        Some(value) => *value,
        None => 0,
    }
}

pub fn cJSON_InitHooks(hooks: Option<&mut cJSON_Hooks>) -> () {
    match hooks {
        Some(value) => *value,
        None => 0,
    }
}

pub fn update_offset(buffer: Option<&mut printbuffer>) -> () {
    match buffer {
        Some(value) => *value,
        None => 0,
    }
}

pub fn buffer_skip_whitespace(buffer: Option<&mut parse_buffer>) -> parse_buffer {
    match buffer {
        Some(value) => *value,
        None => 0,
    }
}

pub fn skip_utf8_bom(buffer: Option<&mut parse_buffer>) -> parse_buffer {
    match buffer {
        Some(value) => *value,
        None => 0,
    }
}

pub fn get_array_item(array: Option<&cJSON>, index: u64) -> cJSON {
    match array {
        Some(value) => *value,
        None => 0,
    }
}

pub fn get_object_item(object: Option<&cJSON>, name: &str, case_sensitive: i32) -> cJSON {
    match object {
        Some(value) => *value,
        None => 0,
    }
}

pub fn cJSON_DetachItemViaPointer(parent: Option<&mut cJSON>, item: Option<&mut cJSON>) -> cJSON {
    match parent {
        Some(value) => *value,
        None => 0,
    }
}
