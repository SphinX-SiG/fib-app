import json
import pytest
import aiohttp

from main import fib
from config import config
from client import FibClient

# class FibClient(object):
#     def __init__(self, host, port, path):
#         self.endpoint = f'ws://{host}:{port}/{path}'
#         self.session = aiohttp.ClientSession()
#
#     def _prepare_message(self, _from, _to, _type):
#         return json.dumps({
#             "action": "count",
#             "from": _from,
#             "to": _to,
#             "type": _type,
#         })
#
#     async def make_request(self, lhv, rhv, _type):
#         message = self._prepare_message(lhv, rhv, _type)
#         response = []
#         async with self.session.ws_connect(self.endpoint) as web_socket:
#             await web_socket.send_str(message)
#             while not web_socket.closed:
#                 _resp = await web_socket.receive()
#                 if web_socket.closed and web_socket.close_code == 1000:
#                     break
#                 _resp = json.loads(_resp.data)
#                 if _resp.get('type') == 'info' and _resp.get('code') == 'EOS' :
#                     break
#                 response.append(_resp)
#         return response

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


def test_around_maximum():
    pass


def test_around_minimum():
    pass
