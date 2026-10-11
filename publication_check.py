"""Check tracked release files for private artifacts and high-confidence credential patterns."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent


def check() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    forbidden = [
        p for p in tracked if p.startswith(("data/", "work/", ".venv/")) or p.endswith(".joblib")
    ]
    assert not forbidden, f"Private artifact paths tracked: {forbidden}"
    pattern = re.compile(
        rb"(?:gh[pousr]_[A-Za-z0-9]{25,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
    )
    for path in tracked:
        if pattern.search((ROOT / path).read_bytes()):
            raise ValueError(f"Credential-like material in {path}; value withheld")
    print(f"Publication gate passed for {len(tracked)} tracked files; private paths excluded.")


if __name__ == "__main__":
    check()
