use nuvo_core::{Refusal, RefusalCode, VERSION};
fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let result = match args.as_slice() {
        [arg] if arg == "--version" || arg == "-V" => {
            println!("nuvo {VERSION}");
            return;
        }
        [arg] if arg == "--help" || arg == "-h" => {
            println!("Nuvo {VERSION}\nUsage: nuvo --version | nuvo doctor\nDoctor reports explicit configuration only; it does not test connectivity.\nSee https://github.com/a-mad-av8r/nuvo");
            return;
        }
        [arg] if arg == "doctor" => nuvo_core::load().map(|config| println!("{}", config.json())),
        _ => Err(Refusal {
            code: RefusalCode::Usage,
            message: "Usage: nuvo --version | nuvo doctor",
        }),
    };
    if let Err(refusal) = result {
        eprintln!("{}", refusal.json());
        std::process::exit(2);
    }
}
