from pathlib import Path

import mm_print


def run(module: str) -> None:
    example_file = Path(Path(__file__).parent.absolute(), "../examples", f"{module}.toml")
    mm_print.toml(toml=example_file.read_text())
