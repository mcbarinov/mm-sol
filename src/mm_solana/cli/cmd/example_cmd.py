from pathlib import Path

import click


def run(module: str) -> None:
    example_file = Path(Path(__file__).parent.absolute(), "../examples", f"{module}.yml")
    click.echo(example_file.read_text())
