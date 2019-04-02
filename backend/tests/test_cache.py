import json
import aioredis

from config import config
from utils.client import FibClient


async def test_redis_cache():
    client = FibClient('localhost', config.get("port"), 'fibo')
    host = config['redis']['host']
    port = config['redis']['port']
    conn = await aioredis.create_connection(f'redis://{host}:{port}', encoding=config['redis']['encoding'])
    _from = 20
    _to = 30
    await conn.execute('DEL', f'{_from}:{_to}')
    response = await client.make_request(_from, _to, 'by_pos')
    cache = await conn.execute('GET', f'{_from}:{_to}')
    parsed_cache = json.loads(cache)
    assert all([lhv == json.loads(rhv) for lhv, rhv in zip(response, parsed_cache)])
