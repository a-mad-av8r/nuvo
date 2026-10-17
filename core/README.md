# core

Nuvo is a modular agent harness. Version 0.1.0 provides a working CLI for explicit provider and Cortex configuration diagnostics: `nuvo --version` and `nuvo doctor`. Doctor reports configuration only, makes no network requests, and returns a typed refusal with exit code 2 when unconfigured. No provider or model is selected by default. Project: https://github.com/a-mad-av8r/nuvo.

The working configuration and typed-refusal API lives in `../packaging/crates/nuvo-core`.
