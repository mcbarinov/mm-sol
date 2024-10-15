import os
import tomllib
from collections.abc import Callable
from typing import TypeVar

import click
import yaml
from click import Context
from jinja2 import Environment, Template, TemplateSyntaxError, meta
from mm_std import print_console
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from rich.console import Console
from rich.table import Table

_jinja_env = Environment(autoescape=True)


class BaseCmdConfig(BaseModel):
    @field_validator("*", mode="before")
    def env_template_validator(cls, v: object) -> object:
        return env_validator(v)

    model_config = ConfigDict(extra="forbid")


def env_validator(v: object) -> object:
    if isinstance(v, str):
        try:
            ast = _jinja_env.parse(v)
            envs = meta.find_undeclared_variables(ast)
            if envs:
                data = {}
                for env in envs:
                    if not os.getenv(env):
                        click.secho(f"can't get environment variable {env}", err=True, fg="red")
                        exit(1)
                    data[env] = os.getenv(env)
                template = Template(v)
                return template.render(data)
        except TemplateSyntaxError as err:
            click.secho(f"jinja syntax error: {err!s}", err=True, fg="red")
            click.secho(v)
            exit(1)
    return v


ConfigImpl = TypeVar("ConfigImpl")  # the variable return type


def parse_config(ctx: Context, config_path: str, config_cls: Callable[..., ConfigImpl]) -> ConfigImpl:
    file_data = read_config_file_or_exit(config_path)
    try:
        if ctx.obj["nodes"]:
            if "nodes" in file_data:
                file_data["nodes"] = ctx.obj["nodes"]
            elif "node" in file_data:
                file_data["node"] = ctx.obj["nodes"][0]
        return config_cls(**file_data)

    except ValidationError as err:
        click.secho(str(err), err=True, fg="red")
        exit(1)


def read_config_file_or_exit(file_path: str) -> dict[str, object]:
    try:
        with open(file_path, "rb") as f:
            if file_path.endswith(".toml"):
                return tomllib.load(f)
            return yaml.full_load(f)  # type:ignore[no-any-return]
    except Exception as err:
        click.secho(f"can't parse config file: {err!s}", fg="red")
        exit(1)


def print_config_and_exit(ctx: Context, config: BaseCmdConfig) -> None:
    if ctx.obj["config"]:
        print_console(config.model_dump(), print_json=True)
        exit(0)


T = TypeVar("T")


def read_config(config_cls: type[T], config_path: str) -> T:
    try:
        with open(config_path) as f:
            config = config_cls(**yaml.full_load(f))
            return config
    except ValidationError as err:
        table = Table(title="config validation errors")
        table.add_column("field")
        table.add_column("message")
        for e in err.errors():
            loc = e["loc"]
            field = str(loc[0]) if len(loc) > 0 else ""
            table.add_row(field, e["msg"])
        console = Console()
        console.print(table)
        exit(1)
