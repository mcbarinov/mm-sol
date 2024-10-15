import random
from decimal import Decimal

from mm_std import print_console, print_json, str_to_list
from pydantic import StrictStr, field_validator

from mm_solana.cli import helpers
from mm_solana.cli.helpers import BaseCmdConfig
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


def run(config_path: str, print_config: bool) -> None:
    config = helpers.read_config(Config, config_path)
    if print_config:
        print_json(config.model_dump())
        exit(0)

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
