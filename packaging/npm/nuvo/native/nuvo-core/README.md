# nuvo-core

Nuvo is a modular agent harness. Version 0.1.0 provides a working CLI for explicit provider and Cortex configuration diagnostics: `nuvo --version` and `nuvo doctor`. Doctor reports configuration only, makes no network requests, and returns a typed refusal with exit code 2 when unconfigured. No provider or model is selected by default. Project: https://github.com/a-mad-av8r/nuvo.

## Install and use

- Rust: `cargo install nuvo-cli --version 0.1.0` (installs `nuvo`).
- npm: `npm install -g nuvo@0.1.0` (Node >=18 plus Rust/Cargo required).
- Python: `python -m pip install nuvo==0.1.0` (Python >=3.9 plus Rust/Cargo required).

npm and Python carry the same Rust sources and compile them offline on first use.
There are no installation scripts, downloaded executables, or third-party runtime dependencies.
A writable user cache is required (`XDG_CACHE_HOME`, otherwise `~/.cache/nuvo/0.1.0`).
Rust 1.83 or newer is required. `nuvo --version` does not read configuration.
`nuvo doctor` returns JSON on stdout when either a provider or Cortex endpoint is set;
this checks selection only, not credentials, endpoint reachability or model availability.

```sh
nuvo --version
NUVO_PROVIDER=your-selected-provider nuvo doctor
NUVO_CORTEX_ENDPOINT=https://your-cortex.example/api nuvo doctor
NUVO_CONFIG=/path/to/nuvo.conf nuvo doctor
```

`NUVO_CONFIG` explicitly selects one UTF-8 key=value file (no implicit search path).
Supported keys are `provider` and `cortex_endpoint`; blank lines and whole-line `#`
comments are allowed. Quotes and interpolation are not supported. Unknown or repeated
keys and malformed lines are errors. Example:

```text
provider=your-selected-provider
cortex_endpoint=https://your-cortex.example/api
```

`NUVO_PROVIDER` and `NUVO_CORTEX_ENDPOINT` override the corresponding file fields;
an explicitly empty value clears that field. A missing or unreadable explicit file
is an error, even if environment overrides exist. Provider identifiers use ASCII
letters/digits and `._-/` (maximum 128 bytes). Endpoints use http(s), a nonempty host,
no whitespace, userinfo, query string or fragment (maximum 2048 bytes).
Use a nonsecret endpoint: doctor displays its configured value. No API tokens are read.
No provider/model defaults or implicit Cortex endpoints are built in.

Failures emit JSON to stderr with `status: refused` and a `code`, and exit 2:
`NUVO_UNCONFIGURED`, `NUVO_INVALID_CONFIGURATION`, `NUVO_CONFIGURATION_READ`,
`NUVO_USAGE`, or launcher failures `NUVO_TOOLCHAIN_MISSING`/`NUVO_BUILD_FAILED`.
This release does not run an agent loop. Future module proposals are in `UPSTREAM.md`.
MIT licensed.
