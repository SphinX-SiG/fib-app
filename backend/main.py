"""This is the simple aiohttp service which calculates elements from Fibonacci sequence,
and stores calculated data in redis.
All available configuration stores in fibonacci.yaml file.
"""


__author__ = 'bychok.vl@gmail.com'


import math
import json
import asyncio
import aioredis
import aiohttp.web

from config import config

EOS = json.dumps({'type': 'info', 'code': 'EOS', 'message': 'End of sequence'})


async def get_redis_conn():
    """
    Function helper which returns connection to redis.
    Returns:
        aioredis.RedisConnection: connection to specified in config redis.
    """
    host = config['redis']['host']
    port = config['redis']['port']
    connection_string = f'redis://{host}:{port}'
    return await aioredis.create_connection(connection_string, encoding=config['redis']['encoding'])


def fib(pos):
    """
    Binet's formula for calculating value by position index

    Args:
        pos(int): index of Fibonacci sequence

    Returns:
        (int): value on index position
    """
    return math.floor((((1 + math.sqrt(5))/2) ** pos - ((1 - math.sqrt(5)) / 2) ** pos) / math.sqrt(5))


async def response_from_cache(cache, ws_obj):
    """
    Method for send cached data to the client

    Args:
        cache(str): serialized array of items from Redis
        ws_obj(WebSocket): web socket object to send response
    """
    parsed_cache = json.loads(cache)
    for item in parsed_cache:
        await ws_obj.send_str(item)
    await ws_obj.send_str(EOS)


def cache_lookup_by_pos(func):
    """
    Decorator checks cache in redis, for requests by position
    """
    async def wrapper(*args, **kwargs):
        conn = await get_redis_conn()
        cache = await conn.execute('GET', f'{args[0]}:{args[1]}')
        if cache:
            return await response_from_cache(cache, **kwargs)
        else:
            return await func(*args, **kwargs)
    return wrapper


def cache_lookup_by_val(func):
    """
    Decorator checks cache in redis, for requests by values
    """
    async def wrapper(*args, **kwargs):
        conn = await get_redis_conn()
        cache = await conn.execute('GET', f'{args[0]}:{args[1]}')
        if cache:
            ws_obj = kwargs.get('so')
            return await response_from_cache(cache, ws_obj)
        else:
            return await func(*args, **kwargs)
    return wrapper


async def store_into_redis(data):
    """
    Write data to redis as cache.
    Args:
        data(dict):
            token(str): '<from>:<to>'
            data(list(dict)):
                type(str): message type
                pos(int): position in sequence
                val(int): value of the item
    """
    conn = await get_redis_conn()
    token = data['token']
    sequence = data['data']
    await conn.execute('SET', token, json.dumps(sequence))


async def check_request(request_data):
    """
    Verify if request is correct and prepare error message if it's not.
    Request correct if:
        borders between min and max values,
        and 'from' field smaller than 'to' field
    Args:
        request_data(dict):
            from(int): left border fo sequence
            to(int): right border of sequence
            type(str): type of calculation

    Returns:
        True, None: if request correct
        False, error_msg(str): if request incorrect
    """
    min_val = config.get('fibonacci').get('min_val')
    max_val = config.get('fibonacci').get('max_val')
    min_pos = config.get('fibonacci').get('min_pos')
    max_pos = config.get('fibonacci').get('max_pos')
    _from = request_data.get('from')
    _to = request_data.get('to')
    _type = request_data.get('type')
    if _type == 'by_val':
        if not(_from < _to and _from < max_val and _from >= min_val and _to > min_val and _to <= max_val):
            ERROR_MSG = json.dumps({
                'type': 'error',
                'message': f'from must be greater than {min_val} and to must be smaller than {max_val}'
            })
            return False, ERROR_MSG
    elif _type == 'by_pos':
        if not(_from < _to and _from < max_pos and _from >= min_pos and _to > min_pos and _to <= max_pos):
            ERROR_MSG = json.dumps({
                'type': 'error',
                'message': f'from must be greater than {min_pos} and to must be smaller than {max_pos}'
            })
            return False, ERROR_MSG
    return True, None


async def websocket_handler(request):
    """
    Request handler for calculation Fibonacci sequence using web socket.
    Parses request data, verify request and choose calculation method.
    Args:
        request(Request):

    Returns:
        WebSocketResponse
    """
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                message = "Connection closed by user request".encode()
                await ws.close(message=message)
            elif 'count' in msg.data:
                parsed_data = msg.json()
                check, err_msg = await check_request(parsed_data)
                if not check:
                    await ws.send_str(err_msg)
                else:
                    if 'by_pos' == parsed_data.get('type'):
                        await fib_handler_by_pos(parsed_data.get('from'), parsed_data.get('to'), ws_obj=ws)
                    elif 'by_val' == parsed_data.get('type'):
                        await fib_handler_by_val(parsed_data.get('from'), parsed_data.get('to'), max=config.get('fibonacci').get('max_val'), so=ws)
            else:
                await ws.send_str(msg.data + '/answer')
    return ws


@cache_lookup_by_pos
async def fib_handler_by_pos(pos_from, pos_to, ws_obj):
    """
    Method calculates Fibonacci sequence between borders represented by positions,
    with help of Binet's formula.
    Args:
        pos_from(int): left border of sequence
        pos_to(int): right border of sequence
        ws_obj(WebSocketResponse): for results

    Returns:

    """
    sequence = []
    for pos in range(pos_from, pos_to+1, 1):
        msg = json.dumps({'type': 'item', 'pos': pos, 'val': fib(pos)})
        await ws_obj.send_str(msg)
        sequence.append(msg)
    result = {'token': f'{pos_from}:{pos_to}', 'data': sequence}
    await store_into_redis(result)
    await ws_obj.send_str(EOS)


@cache_lookup_by_val
async def fib_handler_by_val(*args, **kwargs):
    """ Wrapper function for correct cache checking """
    await fib_handler(*args, **kwargs)


async def fib_handler(_from, _to, first_elem=0, second_elem=1, pos=0, max=None, ws_obj=None, sequence=None):
    """
    Method calculates Fibonacci sequence between borders represented
    by values, using recursion.
    Args:
        _from(int): left boundary of the slice
        _to(int): right boundary of the slice
        first_elem(int): element one
        second_elem(int): element two
        pos(int): position in sequence
        max(int): maximum value for calculation
        ws_obj(WebSocketResponse):
        sequence(list(dict)): collector for result for caching response
    """
    if sequence is None:
        sequence = []
    next_elem = first_elem + second_elem
    if next_elem >= _to or max and next_elem >= max:
        await ws_obj.send_str(EOS)
        result = {'token': f'{_from}:{_to}', 'data': sequence}
        await store_into_redis(result)
    elif _from <= next_elem and next_elem < _to:
        if first_elem == 0 and second_elem == 1:
            await ws_obj.send_str(json.dumps({'type': 'item', 'pos': pos, 'val': first_elem}))
            sequence.append(json.dumps({'type': 'item', 'pos': pos, 'val': first_elem}))
            pos += 1
            await ws_obj.send_str(json.dumps({'type': 'item', 'pos': pos, 'val': second_elem}))
            sequence.append(json.dumps({'type': 'item', 'pos': pos, 'val': first_elem}))
            pos += 1
        msg = json.dumps({'type': 'item', 'pos': pos, 'val': next_elem})
        sequence.append(msg)
        await ws_obj.send_str(msg)
    await fib_handler(_from, _to, second_elem, next_elem, pos + 1, max=max, ws_obj=ws_obj, sequence=sequence)


def main():
    """ Main function for run service """
    loop = asyncio.get_event_loop()
    app = aiohttp.web.Application(loop=loop)
    app['config'] = config
    app.router.add_route('GET', '/fibo', websocket_handler)
    aiohttp.web.run_app(app, host=app['config'].get('host'), port=app['config'].get('port'))


if __name__ == '__main__':
    main()
