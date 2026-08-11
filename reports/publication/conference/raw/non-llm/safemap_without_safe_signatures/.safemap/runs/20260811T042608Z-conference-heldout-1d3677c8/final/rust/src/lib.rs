#![forbid(unsafe_code)]

pub fn csv_get_opts(p: *const csv_parser) -> i32 {
    match p {
        Some(value) => *value,
        None => -1,
    }
}

pub fn csv_set_opts(p: *mut csv_parser, options: u8) -> i32 {
    match p {
        Some(value) => *value,
        None => -1,
    }
}

pub fn csv_init(p: *mut csv_parser, options: u8) -> i32 {
    match p {
        Some(value) => *value,
        None => -1,
    }
}

pub fn csv_free(p: *mut csv_parser) -> () {
    match p {
        Some(value) => *value,
        None => 0,
    }
}

pub fn csv_get_buffer_size(p: *const csv_parser) -> u64 {
    p.entry_size
}

pub fn csv_increase_buffer(p: *mut csv_parser) -> i32 {
    match p {
        Some(value) => *value,
        None => 0,
    }
}

pub fn csv_write2(dest: *mut (), dest_size: u64, src: *const (), src_size: u64, quote: u8) -> u64 {
    match dest {
        Some(value) => *value,
        None => 0,
    }
}

pub fn csv_fwrite2(fp: *mut _IO_FILE, src: *const (), src_size: u64, quote: u8) -> i32 {
    match fp {
        Some(value) => *value,
        None => 0,
    }
}
