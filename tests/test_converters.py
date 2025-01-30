from decimal import Decimal

import pytest

from mm_sol.converters import lamports_to_sol, sol_to_lamports, to_lamports


def test_lamports_to_sol():
    res = lamports_to_sol(272356343007, ndigits=4)
    assert res == Decimal("272.3563")


def test_sol_to_lamports():
    res = sol_to_lamports(Decimal("272.35"))
    assert res == 272350000000


def test_to_lamports():
    assert to_lamports(123) == 123
    assert to_lamports(Decimal("123")) == 123
    assert to_lamports("123") == 123
    assert to_lamports("123.1 sol") == 123.1 * 10**9
    assert to_lamports("123.1sol") == 123.1 * 10**9
    assert to_lamports("12.1t", decimals=6) == 12.1 * 10**6

    with pytest.raises(ValueError):
        to_lamports(Decimal("123.1"))
    with pytest.raises(ValueError):
        to_lamports("10t")
