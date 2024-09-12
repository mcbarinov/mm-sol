import random
from decimal import Decimal

import click
from click import Context
from mm_std import print_console, str_to_list
from pydantic import StrictStr, field_validator

from mm_solana.cli.helpers import BaseCmdConfig, parse_config, print_config_and_exit
from mm_solana.transfer import transfer_sol


class Config(BaseCmdConfig):
    from_address: StrictStr
    private_key: StrictStr
    recipients: list[StrictStr]
    nodes: list[StrictStr]
    amount: Decimal

    @field_validator("recipients", "nodes", mode="before")
    def to_list_validator(cls, v: list[str] | str | None) -> list[str]:
        return str_to_list(v)

    @property
    def random_node(self) -> str:
        return random.choice(self.nodes)


@click.command(name="transfer-sol", help="Transfer SOL")
@click.argument("config_path", type=click.Path(exists=True))
@click.pass_context
def cli(ctx: Context, config_path: str) -> None:
    config = parse_config(ctx, config_path, Config)
    print_config_and_exit(ctx, config)
    result = {}
    for recipient in config.recipients:
        res = transfer_sol(
            from_address=config.from_address,
            private_key_base58=config.private_key,
            recipient_address=recipient,
            amount_sol=config.amount,
            nodes=config.nodes,
        )
        result[recipient] = res.ok_or_err()
    print_console(result, print_json=True)
