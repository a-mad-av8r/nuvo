"""Run the bundled canonical CLI without install hooks or network downloads."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    cache = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "nuvo" / "0.1.0"
    manifest = Path(__file__).resolve().parent / "native" / "nuvo-cli" / "Cargo.toml"
    try:
        result = subprocess.run(["cargo", "run", "--quiet", "--release", "--offline", "--locked", "--manifest-path", str(manifest), "--target-dir", str(cache), "--", *sys.argv[1:]], check=False)
    except OSError:
        print(json.dumps({"status": "refused", "code": "NUVO_TOOLCHAIN_MISSING", "message": "Rust and Cargo are required; see https://github.com/a-mad-av8r/nuvo"}), file=sys.stderr)
        return 2
    if result.returncode == 101 or result.returncode < 0:
        print(json.dumps({"status": "refused", "code": "NUVO_BUILD_FAILED", "message": "Could not build the bundled Nuvo CLI with Cargo."}), file=sys.stderr)
        return 2
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
