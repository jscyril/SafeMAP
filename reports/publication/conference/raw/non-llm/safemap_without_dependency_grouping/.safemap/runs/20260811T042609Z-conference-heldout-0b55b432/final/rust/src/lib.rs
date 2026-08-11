#![forbid(unsafe_code)]

pub fn csv_get_opts(p: Option<&csv_parser>) -> Result<i32, i32> {
    match p {
        Some(value) => Ok(*value),
        None => Err(-1),
    }
}

pub fn csv_set_opts(p: Option<&mut csv_parser>, options: u8) -> Result<i32, i32> {
    match p {
        Some(value) => Ok(*value),
        None => Err(-1),
    }
}

pub fn csv_init(p: Option<&mut csv_parser>, options: u8) -> Result<i32, i32> {
    match p {
        Some(value) => Ok(*value),
        None => Err(-1),
    }
}

pub fn csv_free(p: Option<&mut csv_parser>) -> () {
    match p {
        Some(value) => *value,
        None => 0,
    }
}

pub fn csv_get_buffer_size(p: &csv_parser) -> u64 {
    p.entry_size
}

pub fn csv_increase_buffer(p: Option<&mut csv_parser>) -> Result<i32, i32> {
    match p {
        Some(value) => Ok(*value),
        None => Err(0),
    }
}

pub fn csv_write2(dest: Option<&mut ()>, dest_size: u64, src: Option<&()>, src_size: u64, quote: u8) -> u64 {
    match dest {
        Some(value) => *value,
        None => 0,
    }
}

pub fn csv_fwrite2(fp: Option<&mut _IO_FILE>, src: Option<&()>, src_size: u64, quote: u8) -> i32 {
    match fp {
        Some(value) => *value,
        None => 0,
    }
}
