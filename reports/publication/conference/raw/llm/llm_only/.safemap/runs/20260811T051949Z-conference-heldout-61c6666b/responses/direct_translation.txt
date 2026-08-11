#![forbid(unsafe_code)]

pub const INI_ALLOW_BOM: bool = true;
pub const INI_ALLOW_INLINE_COMMENTS: bool = true;
pub const INI_INLINE_COMMENT_PREFIXES: &str = ";#";
pub const INI_START_COMMENT_PREFIXES: &str = ";#";
pub const INI_ALLOW_MULTILINE: bool = true;
pub const INI_ALLOW_NO_VALUE: bool = true;
pub const INI_STOP_ON_FIRST_ERROR: bool = false;
pub const INI_HANDLER_LINENO: bool = false;
pub const INI_CALL_HANDLER_ON_NEW_SECTION: bool = false;
pub const INI_MAX_LINE: usize = 200;

pub trait IniHandler {
    fn handle(&mut self, section: &str, name: Option<&str>, value: Option<&str>) -> bool;
}

pub trait IniHandlerLineno {
    fn handle(&mut self, section: &str, name: Option<&str>, value: Option<&str>, lineno: i32) -> bool;
}

impl<F> IniHandler for F
where
    F: FnMut(&str, Option<&str>, Option<&str>) -> bool,
{
    fn handle(&mut self, section: &str, name: Option<&str>, value: Option<&str>) -> bool {
        self(section, name, value)
    }
}

pub trait IniReader {
    fn read_line(&mut self, buf: &mut String) -> bool;
}

struct FileIniReader {
    reader: std::io::BufReader<std::fs::File>,
}

impl IniReader for FileIniReader {
    fn read_line(&mut self, buf: &mut String) -> bool {
        buf.clear();
        use std::io::BufRead;
        match self.reader.read_line(buf) {
            Ok(0) => false,
            Ok(_) => true,
            Err(_) => false,
        }
    }
}

struct StringIniReader<'a> {
    ptr: &'a str,
}

impl<'a> IniReader for StringIniReader<'a> {
    fn read_line(&mut self, buf: &mut String) -> bool {
        buf.clear();
        if self.ptr.is_empty() {
            return false;
        }
        if let Some(pos) = self.ptr.find('\n') {
            let (line, rest) = self.ptr.split_at(pos + 1);
            buf.push_str(line);
            self.ptr = rest;
        } else {
            buf.push_str(self.ptr);
            self.ptr = "";
        }
        true
    }
}

fn ini_rstrip(s: &str) -> &str {
    s.trim_end_matches(|c: char| c.is_ascii_whitespace())
}

fn ini_lskip(s: &str) -> &str {
    s.trim_start_matches(|c: char| c.is_ascii_whitespace())
}

fn ini_find_chars_or_comment<'a>(s: &'a str, chars: Option<&str>) -> &'a str {
    if INI_ALLOW_INLINE_COMMENTS {
        let mut was_space = false;
        let mut indices = s.char_indices();
        while let Some((idx, c)) = indices.next() {
            if let Some(chrs) = chars {
                if chrs.contains(c) {
                    return &s[idx..];
                }
            }
            if was_space && INI_INLINE_COMMENT_PREFIXES.contains(c) {
                return &s[idx..];
            }
            was_space = c.is_ascii_whitespace();
        }
        &s[s.len()..]
    } else {
        let mut indices = s.char_indices();
        while let Some((idx, c)) = indices.next() {
            if let Some(chrs) = chars {
                if chrs.contains(c) {
                    return &s[idx..];
                }
            }
        }
        &s[s.len()..]
    }
}

pub fn ini_parse_stream<R: IniReader, H: IniHandler>(
    mut reader: R,
    mut handler: H,
) -> i32 {
    let mut line = String::new();
    let mut section = String::new();
    let mut prev_name = String::new();

    let mut lineno = 0;
    let mut error = 0;

    let mut has_next = reader.read_line(&mut line);
    while has_next {
        lineno++;

        let mut offset = line.len();
        while offset < INI_MAX_LINE && !line.ends_with('\n') {
            let mut next_part = String::new();
            if !reader.read_line(&mut next_part) {
                break;
            }
            if next_part.is_empty() {
                break;
            }
            line.push_str(&next_part);
            offset = line.len();
        }

        if offset >= INI_MAX_LINE && !line.ends_with('\n') {
            let mut abyss = String::new();
            while reader.read_line(&mut abyss) {
                if error == 0 {
                    error = lineno;
                }
                if abyss.ends_with('\n') {
                    break;
                }
            }
        }

        let mut start_str = line.as_str();

        if INI_ALLOW_BOM && lineno == 1 && start_str.starts_with("\u{FEFF}") {
            start_str = &start_str[3..];
        }

        let trimmed_l = ini_lskip(start_str);
        let start = ini_rstrip(trimmed_l);

        let first_char = start.chars().next();

        if let Some(fc) = first_char {
            if INI_START_COMMENT_PREFIXES.contains(fc) {
                // Start-of-line comment
            } else if INI_ALLOW_MULTILINE && !prev_name.is_empty() && !start.is_empty() && start.as_ptr() != start_str.as_ptr() {
                let mut content = start;
                if INI_ALLOW_INLINE_COMMENTS {
                    let end = ini_find_chars_or_comment(content, None);
                    let end_idx = end.as_ptr() as usize - content.as_ptr() as usize;
                    content = &content[..end_idx];
                    content = ini_rstrip(content);
                }
                let res = handler.handle(&section, Some(&prev_name), Some(content));
                if !res && error == 0 {
                    error = lineno;
                }
            } else if fc == '[' {
                let end = ini_find_chars_or_comment(&start[1..], Some("]"));
                if end.starts_with(']') {
                    let section_name = &start[1..start.len() - end.len() + 1];
                    section = section_name.to_string();
                    if INI_ALLOW_MULTILINE {
                        prev_name.clear();
                    }
                    if INI_CALL_HANDLER_ON_NEW_SECTION {
                        let res = handler.handle(&section, None, None);
                        if !res && error == 0 {
                            error = lineno;
                        }
                    }
                } else if error == 0 {
                    error = lineno;
                }
            } else {
                let end = ini_find_chars_or_comment(start, Some("=:"));
                if end.starts_with('=') || end.starts_with(':') {
                    let name_part = &start[..start.len() - end.len()];
                    let name = ini_rstrip(name_part);
                    let mut value = &end[1..];
                    if INI_ALLOW_INLINE_COMMENTS {
                        let val_end = ini_find_chars_or_comment(value, None);
                        let val_end_idx = val_end.as_ptr() as usize - value.as_ptr() as usize;
                        value = &value[..val_end_idx];
                    }
                    value = ini_lskip(value);
                    value = ini_rstrip(value);

                    if INI_ALLOW_MULTILINE {
                        prev_name = name.to_string();
                    }
                    let res = handler.handle(&section, Some(name), Some(value));
                    if !res && error == 0 {
                        error = lineno;
                    }
                } else if INI_ALLOW_NO_VALUE {
                    let name = ini_rstrip(start);
                    let res = handler.handle(&section, Some(name), None);
                    if !res && error == 0 {
                        error = lineno;
                    }
                } else if error == 0 {
                    error = lineno;
                }
            }
        }

        if INI_STOP_ON_FIRST_ERROR && error != 0 {
            break;
        }

        has_next = reader.read_line(&mut line);
    }

    error
}

pub fn ini_parse_file<H: IniHandler>(file: std::fs::File, handler: H) -> i32 {
    let reader = FileIniReader {
        reader: std::io::BufReader::new(file),
    };
    ini_parse_stream(reader, handler)
}

pub fn ini_parse<P: AsRef<std::path::Path>, H: IniHandler>(filename: P, handler: H) -> i32 {
    let file = match std::fs::File::open(filename) {
        Ok(f) => f,
        Err(_) => return -1,
    };
    ini_parse_file(file, handler)
}

pub fn ini_parse_string<H: IniHandler>(string: &str, handler: H) -> i32 {
    let reader = StringIniReader { ptr: string };
    ini_parse_stream(reader, handler)
}

pub fn ini_parse_string_length<H: IniHandler>(string: &str, length: usize, handler: H) -> i32 {
    let slice = if length >= string.len() {
        string
    } else {
        let mut idx = length;
        while idx > 0 && !string.is_char_boundary(idx) {
            idx -= 1;
        }
        &string[..idx]
    };
    ini_parse_string(slice, handler)
}
