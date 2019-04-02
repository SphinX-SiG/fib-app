import pytest

from main import fib
from config import config
from utils.client import FibClient


@pytest.fixture
def fib_pos():
    return [fib(n) for n in [3, 4, 5, 6]]


def test_fib(fib_pos):
    check_list = [2, 3, 5, 8]
    check_res = fib_pos
    assert all([lhv == rhv for lhv, rhv in zip(check_list, check_res)])


def test_fib_calc():
    assert fib(9) + fib(10) == fib(11)
    assert fib(10) + fib(11) == fib(12)
    assert fib(11) + fib(12) == fib(13)



async def test_by_pos_from_cli():
    expected = [
        2, 3, 5, 8, 13, 21,
        34, 55, 89, 144, 233,
        377, 610, 987, 1597,
        2584, 4181, 6765
    ]
    client = FibClient('localhost', config.get("port"), 'fibo')
    response = await client.make_request(3, 20, 'by_pos')
    assert expected == [i.get('val') for i in response]


async def test_by_val_from_cli():
    expected = [2584, 4181, 6765, 10946, 17711]
    client = FibClient('localhost', config.get("port"), 'fibo')
    response = await client.make_request(2400, 26000, 'by_val')
    assert expected == [i.get('val') for i in response]


async def test_around_borders():
    client = FibClient('localhost', config.get("port"), 'fibo')
    borders = config.get('fibonacci')
    min_pos, max_pos = borders.get('min_pos'), borders.get('max_pos')
    min_val, max_val = borders.get('min_val'), borders.get('max_val')
    by_val_min = await client.make_request(min_val-20, 20, 'by_val')
    assert by_val_min[0].get('type') == 'error'
    by_val_max = await client.make_request(24000, max_val+150, 'by_val')
    assert by_val_max[0].get('type') == 'error'
    by_pos_min = await client.make_request(min_pos-5, 5, 'by_pos')
    assert by_pos_min[0].get('type') == 'error'
    by_pos_max = await client.make_request(0, max_pos+5, 'by_pos')
    assert by_pos_max[0].get('type') == 'error'
