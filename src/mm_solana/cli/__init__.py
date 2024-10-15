# import click
# from click import Context
# from click_aliases import ClickAliasedGroup
#
# from mm_solana.cli.cmd import (
#     balance_cmd,
#     example_cmd,
#     generate_accounts_cmd,
#     keypair_cmd,
#     transfer_sol_cmd,
# )
# from mm_solana.cli.helpers import get_version
#
#
# @click.group(cls=ClickAliasedGroup)
# @click.option("-c", "--config/--no-config", "config_", default=False, help="Print config and exit")
# @click.option("-n", "--node", multiple=True, help="List of JSON RPC nodes, it overwrites node/nodes field in config")
# @click.version_option(get_version(), help="Show the version and exit")
# @click.help_option(help="Show this message and exit")
# @click.pass_context
# def cli(ctx: Context, config_: bool, node: list[str]) -> None:
#     ctx.ensure_object(dict)
#     ctx.obj["config"] = config_
#     ctx.obj["nodes"] = node
#
#
# # noinspection PyTypeChecker
# cli.add_command(balance_cmd.cli)
# # noinspection PyTypeChecker
# cli.add_command(example_cmd.cli)
# # noinspection PyTypeChecker
# cli.add_command(generate_accounts_cmd.cli)
# # noinspection PyTypeChecker
# cli.add_command(keypair_cmd.cli)
# # noinspection PyTypeChecker
# cli.add_command(transfer_sol_cmd.cli)
