# Registry packaging

Nuvo is a modular agent harness. Version 0.1.0 provides a working CLI for explicit provider and Cortex configuration diagnostics: `nuvo --version` and `nuvo doctor`. Doctor reports configuration only, makes no network requests, and returns a typed refusal with exit code 2 when unconfigured. No provider or model is selected by default. Project: https://github.com/a-mad-av8r/nuvo.

Run `python3 scripts/prepare.py` after changing canonical Rust sources. Bundled native copies are generated, not independent implementations. Aliases depend only on canonical nuvo. Stage crates outside the parent Helix Git context before packaging to avoid publishing parent VCS metadata. A packed archive or a successful local build does not reserve a registry name.
