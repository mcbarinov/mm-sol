import pytest

from mm_sol.cli import calcs
from mm_sol.converters import to_lamports


def test_calc_var_value():
    assert calcs.calc_var_value("100") == 100
    assert calcs.calc_var_value("10 + 2 - 5") == 7
    assert calcs.calc_var_value("10 - random(2,2)") == 8
    assert calcs.calc_var_value("1.5base + 1", var_value=10, var_name="base") == 16
    assert calcs.calc_var_value("1.5estimate + 1", var_value=10, var_name="estimate") == 16
    assert calcs.calc_var_value("12.2 sol") == to_lamports("12.2sol")
    assert calcs.calc_var_value("12.2 t", decimals=6) == 12.2 * 10**6

    with pytest.raises(ValueError):
        calcs.calc_var_value("fff")
    with pytest.raises(ValueError):
        calcs.calc_var_value("12.3 sol + base", var_name="base")
    with pytest.raises(ValueError):
        calcs.calc_var_value("1.5estimate + 1", var_value=10)
    with pytest.raises(ValueError):
        calcs.calc_var_value("1.1t")


# def test_calc_function_args():
#     res = calcs.calc_function_args('["xxx", random(100,200), 100, "aaa", random(1,3)]')
#     assert json.loads(res)[1] >= 100
