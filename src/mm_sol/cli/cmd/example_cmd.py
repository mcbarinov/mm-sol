from pathlib import Path

from mm_std import pretty_print_toml


def run(module: str) -> None:
    example_file = Path(Path(__file__).parent.absolute(), "../examples", f"{module}.toml")
    pretty_print_toml(example_file.read_text())
