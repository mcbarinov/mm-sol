"""Example config display command."""

from pathlib import Path

from mm_clikit import print_toml


def run(module: str) -> None:
    """Print the example TOML configuration for the given command module."""
    example_file = Path(Path(__file__).parent.absolute(), "../examples", f"{module}.toml")
    print_toml(example_file.read_text())
