#![forbid(unsafe_code)]

use safemap_generated::sqr;

const MAX_I: i32 = 65_536;

fn norm_squared(real: f64, imaginary: f64) -> f64 {
    sqr(real) + sqr(imaginary)
}

fn iterations(c_real: f64, c_imaginary: f64) -> i32 {
    let mut real = c_real;
    let mut imaginary = c_imaginary;
    let mut iteration = 1;
    while norm_squared(real, imaginary) <= 4.0 {
        let previous = iteration;
        iteration += 1;
        if previous >= MAX_I {
            break;
        }
        let next_real = real * real - imaginary * imaginary + c_real;
        let next_imaginary = 2.0 * real * imaginary + c_imaginary;
        real = next_real;
        imaginary = next_imaginary;
    }
    iteration
}

fn main() {
    for row in -39..39 {
        for column in -39..39 {
            let c_real = f64::from(row) / 40.0 - 0.5;
            let c_imaginary = f64::from(column) / 40.0;
            let pixel = if iterations(c_real, c_imaginary) > MAX_I {
                '*'
            } else {
                ' '
            };
            print!("{pixel}");
        }
        println!();
    }
}
