from enum import Enum
from typing import Annotated

import typer
from mm_std import print_plain

from .cmd import balance_cmd, example_cmd, node_cmd, transfer_sol_cmd
from .cmd.wallet import keypair_cmd, new_cmd

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False, add_completion=False)

wallet_app = typer.Typer(no_args_is_help=True, help="Wallet commands: generate new accounts, private to address")
app.add_typer(wallet_app, name="wallet")
app.add_typer(wallet_app, name="w", hidden=True)


def version_callback(value: bool) -> None:
    if value:
        import importlib.metadata

        print_plain(f"mm-solana: {importlib.metadata.version('mm-solana')}")
        raise typer.Exit


@app.callback()
def main(_version: bool = typer.Option(None, "--version", callback=version_callback, is_eager=True)) -> None:
    pass


class ConfigExample(str, Enum):
    balance = "balance"
    transfer_sol = "transfer-sol"


@app.command(name="example", help="Print an example of config for a command")
def example_command(command: Annotated[ConfigExample, typer.Argument()]) -> None:
    example_cmd.run(command.value)


@app.command(name="balance", help="Print SOL and tokens balances")
def balance_command(
    config_path: str, print_config: Annotated[bool, typer.Option("--config", "-c", help="Print config and exit")] = False
) -> None:
    balance_cmd.run(config_path, print_config)


@app.command(name="transfer-sol", help="Transfer SOL")
def transfer_sol_command(
    config_path: str, print_config: Annotated[bool, typer.Option("--config", "-c", help="Print config and exit")] = False
) -> None:
    transfer_sol_cmd.run(config_path, print_config)


@app.command(name="node", help="Check RPC urls")
def node_command(
    urls: Annotated[list[str], typer.Argument()],
    proxy: Annotated[str | None, typer.Option("--proxy", "-p", help="Proxy")] = None,
) -> None:
    node_cmd.run(urls, proxy)


@wallet_app.command(name="new", help="Generate new accounts")
def generate_accounts_command(
    limit: Annotated[int, typer.Option("--limit", "-l")] = 5,
    array: Annotated[bool, typer.Option("--array", help="Print private key in the array format.")] = False,
) -> None:
    new_cmd.run(limit, array)


@wallet_app.command(name="keypair", help="Print public, private_base58, private_arr by a private key")
def keypair_command(private_key: str) -> None:
    keypair_cmd.run(private_key)


if __name__ == "__main_":
    app()
