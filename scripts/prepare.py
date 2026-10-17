#!/usr/bin/env python3
"""Regenerate registry wrappers' native source bundles from the two canonical crates."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PARAGRAPH = "Nuvo is a modular agent harness. Version 0.1.0 provides a working CLI for explicit provider and Cortex configuration diagnostics: `nuvo --version` and `nuvo doctor`. Doctor reports configuration only, makes no network requests, and returns a typed refusal with exit code 2 when unconfigured. No provider or model is selected by default. Project: https://github.com/a-mad-av8r/nuvo."
DETAILS = """
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
"""

def main():
    readme = '# Nuvo\n\n' + PARAGRAPH + '\n' + DETAILS
    (ROOT/'README.md').write_text(readme)
    for registry, names in [('npm',['nuvo','nuvo-ai','nuvo-cli']), ('pypi',['nuvo','nuvo-ai','nuvo-cli']), ('crates',['nuvo-core','nuvo-cli'])]:
        for name in names:
            path = ROOT/'packaging'/registry/name
            alias = registry in ('npm','pypi') and name != 'nuvo'
            extra = '\nCompatibility name: install the canonical `nuvo` package: https://github.com/a-mad-av8r/nuvo.\n' if alias else DETAILS
            (path/'README.md').write_text('# '+name+'\n\n'+PARAGRAPH+'\n'+extra)
            if registry == 'npm':
                meta=json.loads((path/'package.json').read_text())
                meta.update(version='0.1.0', description='Explicit provider and Cortex configuration diagnostics for Nuvo', homepage='https://github.com/a-mad-av8r/nuvo')
                meta.pop('main', None)
                meta['files']=['README.md','LICENSE']
                if alias:
                    meta['dependencies']={'nuvo':'0.1.0'}
                else:
                    meta['bin']={'nuvo':'bin/nuvo.js'}
                    meta['engines']={'node':'>=18'}
                    meta['files']+=['bin/','native/']
                (path/'package.json').write_text(json.dumps(meta,indent=2)+'\n')
                (path/'index.js').unlink(missing_ok=True)
            elif registry == 'pypi':
                package=name.replace('-','_')
                deps='["nuvo==0.1.0"]' if alias else '[]'
                text='[build-system]\nrequires = ["setuptools>=77"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\n'
                text+=f'name = "{name}"\nversion = "0.1.0"\ndescription = "Explicit provider and Cortex configuration diagnostics for Nuvo"\nreadme = "README.md"\nrequires-python = ">=3.9"\nlicense = "MIT"\nlicense-files = ["LICENSE"]\ndependencies = {deps}\n\n[project.urls]\nHomepage = "https://github.com/a-mad-av8r/nuvo"\nRepository = "https://github.com/a-mad-av8r/nuvo"\n'
                if alias:
                    text+='\n[tool.setuptools]\npackages = []\n'
                    (path/package/'__init__.py').unlink(missing_ok=True)
                else:
                    text+='\n[project.scripts]\nnuvo = "nuvo.__main__:main"\n\n[tool.setuptools]\npackages = ["nuvo"]\n\n[tool.setuptools.package-data]\nnuvo = ["native/**/*"]\n'
                    (path/'MANIFEST.in').write_text('recursive-include nuvo/native *.rs *.toml *.lock *.md LICENSE\n')
                (path/'pyproject.toml').write_text(text)
    for destination in [ROOT/'packaging/npm/nuvo/native', ROOT/'packaging/pypi/nuvo/nuvo/native']:
        for name in ['nuvo-core','nuvo-cli']:
            source=ROOT/'packaging/crates'/name
            for filename in ['Cargo.toml','Cargo.lock','README.md','LICENSE','src/lib.rs' if name=='nuvo-core' else 'src/main.rs']:
                src=source/filename
                if src.exists():
                    dst=destination/name/filename
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(src,dst)
    (ROOT/'packaging/README.md').write_text('# Registry packaging\n\n'+PARAGRAPH+'\n\nRun `python3 scripts/prepare.py` after changing canonical Rust sources. Bundled native copies are generated, not independent implementations. Aliases depend only on canonical nuvo. Stage crates outside the parent Helix Git context before packaging to avoid publishing parent VCS metadata. A packed archive or a successful local build does not reserve a registry name.\n')
    for module, text in {'core':'The working configuration and typed-refusal API lives in `../packaging/crates/nuvo-core`.', 'cli':'The working canonical CLI lives in `../packaging/crates/nuvo-cli`; npm/PyPI launchers delegate to it.', 'cortex-adapter':'This release reports an explicitly selected Cortex endpoint; no adapter or network client is implemented.', 'fusion':'Future optional module; not implemented in 0.1.0.'}.items():
        (ROOT/module/'README.md').write_text('# '+module+'\n\n'+PARAGRAPH+'\n\n'+text+'\n')

if __name__=='__main__': main()
