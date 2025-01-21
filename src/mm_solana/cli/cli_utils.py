import sys

from mm_std import BaseConfig, print_json


def print_config_and_exit(exit_: bool, config: BaseConfig, exclude: set[str] | None = None) -> None:
    if exit_:
        print_json(config.model_dump(exclude=exclude))
        sys.exit(0)
