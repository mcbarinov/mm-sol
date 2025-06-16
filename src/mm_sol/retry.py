from mm_result import Result
from mm_web3 import Nodes, Proxies, retry_with_node_and_proxy
from solders.solders import Pubkey, Signature

from mm_sol import rpc, spl_token, transfer


async def get_sol_balance(retries: int, nodes: Nodes, proxies: Proxies, *, address: str, timeout: float = 5) -> Result[int]:
    return await retry_with_node_and_proxy(
        retries,
        nodes,
        proxies,
        lambda node, proxy: rpc.get_balance(node=node, address=address, timeout=timeout, proxy=proxy),
    )


async def get_token_balance(
    retries: int,
    nodes: Nodes,
    proxies: Proxies,
    *,
    owner: str,
    token: str,
    token_account: str | None = None,
    timeout: float = 5,
) -> Result[int]:
    return await retry_with_node_and_proxy(
        retries,
        nodes,
        proxies,
        lambda node, proxy: spl_token.get_balance(
            node,
            owner=owner,
            token=token,
            token_account=token_account,
            timeout=timeout,
            proxy=proxy,
        ),
    )


async def transfer_token(
    retries: int,
    nodes: Nodes,
    proxies: Proxies,
    *,
    token_mint_address: str | Pubkey,
    from_address: str | Pubkey,
    private_key: str,
    to_address: str | Pubkey,
    amount: int,  # smallest unit
    decimals: int,
    timeout: float = 10,
    create_token_account_if_not_exists: bool = True,
) -> Result[Signature]:
    return await retry_with_node_and_proxy(
        retries,
        nodes,
        proxies,
        lambda node, proxy: transfer.transfer_token(
            node=node,
            token_mint_address=token_mint_address,
            from_address=from_address,
            private_key=private_key,
            to_address=to_address,
            amount=amount,
            decimals=decimals,
            proxy=proxy,
            timeout=timeout,
            create_token_account_if_not_exists=create_token_account_if_not_exists,
        ),
    )


async def transfer_sol(
    retries: int,
    nodes: Nodes,
    proxies: Proxies,
    *,
    from_address: str,
    private_key: str,
    to_address: str,
    lamports: int,
    timeout: float = 10,
) -> Result[Signature]:
    return await retry_with_node_and_proxy(
        retries,
        nodes,
        proxies,
        lambda node, proxy: transfer.transfer_sol(
            node=node,
            proxy=proxy,
            from_address=from_address,
            to_address=to_address,
            lamports=lamports,
            private_key=private_key,
            timeout=timeout,
        ),
    )


async def get_token_decimals(retries: int, nodes: Nodes, proxies: Proxies, *, token: str, timeout: float = 5) -> Result[int]:
    return await retry_with_node_and_proxy(
        retries,
        nodes,
        proxies,
        lambda node, proxy: spl_token.get_decimals(node, token=token, proxy=proxy, timeout=timeout),
    )
