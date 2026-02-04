"""Conversion utilities between SOL, lamports, and token smallest units."""

from decimal import Decimal


def lamports_to_sol(lamports: int, ndigits: int = 4) -> Decimal:
    """Convert lamports to SOL with the specified decimal precision."""
    if lamports == 0:
        return Decimal(0)
    return Decimal(str(round(lamports / 10**9, ndigits=ndigits)))


def to_token(smallest_unit_value: int, decimals: int, ndigits: int = 4) -> Decimal:
    """Convert a token's smallest unit value to a human-readable Decimal."""
    if smallest_unit_value == 0:
        return Decimal(0)
    return Decimal(str(round(smallest_unit_value / 10**decimals, ndigits=ndigits)))


def sol_to_lamports(sol: Decimal) -> int:
    """Convert SOL amount to lamports."""
    return int(sol * 10**9)


def to_lamports(value: str | int | Decimal, decimals: int | None = None) -> int:
    """Parse a value into lamports. Supports raw int, Decimal, or string with 'sol'/'t' suffix."""
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        if value != value.to_integral_value():
            raise ValueError(f"value must be integral number: {value}")
        return int(value)
    if isinstance(value, str):
        value = value.lower().replace(" ", "").strip()
        if value.endswith("sol"):
            value = value.replace("sol", "")
            return sol_to_lamports(Decimal(value))
        if value.endswith("t"):
            if decimals is None:
                raise ValueError("t without decimals")
            value = value.removesuffix("t")
            return int(Decimal(value) * 10**decimals)
        if value.isdigit():
            return int(value)
        raise ValueError("wrong value " + value)

    raise ValueError(f"value has a wrong type: {type(value)}")
