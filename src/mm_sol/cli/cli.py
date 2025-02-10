from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from mm_std import print_plain

from mm_sol.account import PHANTOM_DERIVATION_PATH

from . import cli_utils
from .cmd import balance_cmd, balances_cmd, example_cmd, node_cmd, transfer_cmd
from .cmd.transfer_cmd import TransferCmdParams
from .cmd.wallet import keypair_cmd, mnemonic_cmd

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False, add_completion=False)

wallet_app = typer.Typer(
    no_args_is_help=True, help="Wallet-related commands: generate new accounts, derive addresses from private keys, and more"
)
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
    transfer = "transfer"


@app.command(name="example", help="Displays an example configuration for a command")
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


@app.command(name="balances", help="Displays SOL and token balances for multiple accounts")
def balances_command(
    config_path: Path, print_config: Annotated[bool, typer.Option("--config", "-c", help="Print config and exit")] = False
) -> None:
    balances_cmd.run(config_path, print_config)


@app.command(name="transfer", help="Transfers SOL or SPL tokens, supporting multiple routes, delays, and expression-based values")
def transfer_command(
    config_path: Path,
    print_balances: bool = typer.Option(False, "--balances", "-b", help="Print balances and exit"),
    print_transfers: bool = typer.Option(False, "--transfers", "-t", help="Print transfers (from, to, value) and exit"),
    print_config: bool = typer.Option(False, "--config", "-c", help="Print config and exit"),
    config_verbose: bool = typer.Option(False, "--config-verbose", help="Print config in verbose mode and exit"),
    emulate: bool = typer.Option(False, "--emulate", "-e", help="Emulate transaction posting"),
    no_confirmation: bool = typer.Option(False, "--no-confirmation", "-nc", help="Do not wait for confirmation"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Print debug info"),
) -> None:
    transfer_cmd.run(
        TransferCmdParams(
            config_path=config_path,
            print_balances=print_balances,
            print_transfers=print_transfers,
            debug=debug,
            no_confirmation=no_confirmation,
            emulate=emulate,
            print_config_and_exit=print_config or config_verbose,
            print_config_verbose=config_verbose,
        )
    )


@app.command(name="node", help="Checks RPC URLs for availability and status")
def node_command(
    urls: Annotated[list[str], typer.Argument()],
    proxy: Annotated[str | None, typer.Option("--proxy", "-p", help="Proxy")] = None,
) -> None:
    node_cmd.run(urls, proxy)


@wallet_app.command(name="mnemonic", help="Derive accounts from a mnemonic")
@wallet_app.command(name="m", hidden=True)
def wallet_mnemonic_command(  # nosec
    mnemonic: Annotated[str, typer.Option("--mnemonic", "-m")] = "",
    passphrase: Annotated[str, typer.Option("--passphrase", "-p")] = "",
    derivation_path: Annotated[str, typer.Option("--path")] = PHANTOM_DERIVATION_PATH,
    words: int = typer.Option(12, "--words", "-w", help="Number of mnemonic words"),
    limit: int = typer.Option(5, "--limit", "-l"),
) -> None:
    mnemonic_cmd.run(mnemonic, passphrase, words, derivation_path, limit)


@wallet_app.command(name="keypair", help="Print public, private_base58, private_arr by a private key")
def keypair_command(private_key: str) -> None:
    keypair_cmd.run(private_key)


if __name__ == "__main_":
    app()
