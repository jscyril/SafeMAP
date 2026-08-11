#![forbid(unsafe_code)]

pub fn csv_get_opts(p: &csv_parser) -> Result<i32, i32> {
    -1
}

pub fn csv_set_opts(p: &mut csv_parser, options: u8) -> Result<i32, i32> {
    -1
}

pub fn csv_init(p: &mut csv_parser, options: u8) -> Result<i32, i32> {
    -1
}

pub fn csv_get_buffer_size(p: &csv_parser) -> u64 {
    p.entry_size
}

pub fn csv_write2(dest: &mut (), dest_size: u64, src: &(), src_size: u64, quote: u8) -> u64 {
    0
}
