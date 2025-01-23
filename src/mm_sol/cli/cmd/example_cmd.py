from pathlib import Path

from mm_std import print_plain


def run(module: str) -> None:
    example_file = Path(Path(__file__).parent.absolute(), "../examples", f"{module}.yml")
    print_plain(example_file.read_text())
