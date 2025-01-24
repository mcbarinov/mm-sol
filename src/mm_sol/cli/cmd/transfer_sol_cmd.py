import random
from decimal import Decimal

from mm_std import BaseConfig, print_console, str_to_list
from pydantic import StrictStr, field_validator

from mm_sol.cli import cli_utils
from mm_sol.transfer import transfer_sol_with_retries


class Config(BaseConfig):
    from_address: StrictStr
    private_key: StrictStr
    recipients: list[StrictStr]
    nodes: list[StrictStr]
    amount: Decimal
    proxies_url: str | None

    @field_validator("recipients", "nodes", mode="before")
    def to_list_validator(cls, v: list[str] | str | None) -> list[str]:
        return str_to_list(v)

    @property
    def random_node(self) -> str:
        return random.choice(self.nodes)


def run(config_path: str, print_config: bool) -> None:
    config = Config.read_config_or_exit(config_path)
    cli_utils.print_config_and_exit(print_config, config)

    result = {}
    for recipient in config.recipients:
        res = transfer_sol_with_retries(
            nodes=config.nodes,
            from_address=config.from_address,
            private_key=config.private_key,
            to_address=recipient,
            value=config.amount,
            proxies=cli_utils.load_proxies_from_url(config.proxies_url),
        )
        result[recipient] = res.ok_or_err()
    print_console(result, print_json=True)
