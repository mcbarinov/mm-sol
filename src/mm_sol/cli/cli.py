from enum import Enum
from typing import Annotated

import typer
from mm_std import print_plain

from . import cli_utils
from .cmd import balance_cmd, balances_cmd, example_cmd, node_cmd, transfer_sol_cmd, transfer_token_cmd
from .cmd.wallet import keypair_cmd, new_cmd

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False, add_completion=False)

wallet_app = typer.Typer(no_args_is_help=True, help="Wallet commands: generate new accounts, private to address")
app.add_typer(wallet_app, name="wallet")
app.add_typer(wallet_app, name="w", hidden=True)


def version_callback(value: bool) -> None:
    if value:
        print_plain(f"mm-sol: {cli_utils.get_version()}")
        raise typer.Exit


@app.callback()
def main(_version: bool = typer.Option(None, "--version", callback=version_callback, is_eager=True)) -> None:
    pass


class ConfigExample(str, Enum):
    balances = "balances"
    transfer_sol = "transfer-sol"


@app.command(name="example", help="Print an example of config for a command")
def example_command(command: Annotated[ConfigExample, typer.Argument()]) -> None:
    example_cmd.run(command.value)


@app.command(name="balance", help="Gen account balance")
def balance_command(
    wallet_address: Annotated[str, typer.Argument()],
    token_address: Annotated[str | None, typer.Option("--token", "-t")] = None,
    rpc_url: Annotated[str, typer.Option("--url", "-u", envvar="MM_SOL_RPC_URL")] = "",  # nosec
    proxies_url: Annotated[str, typer.Option("--proxies-url", envvar="MM_SOL_PROXIES_URL")] = "",  # nosec
    lamport: bool = typer.Option(False, "--lamport", "-l", help="Print balances in lamports"),
) -> None:
    balance_cmd.run(rpc_url, wallet_address, token_address, lamport, proxies_url)


@app.command(name="balances", help="Print SOL and token balances for accounts")
def balances_command(
    config_path: str, print_config: Annotated[bool, typer.Option("--config", "-c", help="Print config and exit")] = False
) -> None:
    balances_cmd.run(config_path, print_config)


@app.command(name="transfer-sol", help="Transfer SOL from one or many accounts")
def transfer_sol_command(
    config_path: str,
    print_balances: bool = typer.Option(False, "--balances", "-b", help="Print balances and exit"),
    print_config: bool = typer.Option(False, "--config", "-c", help="Print config and exit"),
    emulate: bool = typer.Option(False, "--emulate", "-e", help="Emulate transaction posting"),
    no_confirmation: bool = typer.Option(False, "--no-confirmation", "-nc", help="Do not wait for confirmation"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Print debug info"),
) -> None:
    transfer_sol_cmd.run(
        config_path,
        print_balances=print_balances,
        print_config=print_config,
        debug=debug,
        no_confirmation=no_confirmation,
        emulate=emulate,
    )


@app.command(name="transfer-token", help="Transfer token from one or many accounts")
def transfer_token_command(
    config_path: str,
    print_balances: bool = typer.Option(False, "--balances", "-b", help="Print balances and exit"),
    print_config: bool = typer.Option(False, "--config", "-c", help="Print config and exit"),
    emulate: bool = typer.Option(False, "--emulate", "-e", help="Emulate transaction posting"),
    no_confirmation: bool = typer.Option(False, "--no-confirmation", "-nc", help="Do not wait for confirmation"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Print debug info"),
) -> None:
    transfer_token_cmd.run(
        config_path,
        print_balances=print_balances,
        print_config=print_config,
        debug=debug,
        no_confirmation=no_confirmation,
        emulate=emulate,
    )


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
