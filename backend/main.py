import math
import json
import asyncio
import aiohttp.web
import aioredis

from config import config


async def get_redis_conn():
    host = config['redis']['host']
    port = config['redis']['port']
    connection_string = f'redis://{host}:{port}'
    return await aioredis.create_connection(connection_string, encoding=config['redis']['encoding'])


def fib(n):
    return math.floor((((1 + math.sqrt(5))/2)**n-((1 - math.sqrt(5))/2)**n)/math.sqrt(5))


async def response_from_cache(cache, so):
    parsed_cache = json.loads(cache)
    for item in parsed_cache:
        await so.send_str(item)
    await so.send_str(json.dumps({'type': 'info', 'code': 'EOS', 'message': 'End of sequence'}))


def cache_lookup_by_pos(func):
    async def wrapper(*args, **kwargs):
        conn = await get_redis_conn()
        cache = await conn.execute('GET', f'{args[0]}:{args[1]}')
        if cache:
            return await response_from_cache(cache, **kwargs)
        else:
            return await func(*args, **kwargs)
    return wrapper


def cache_lookup_by_val(func):
    async def wrapper(*args, **kwargs):
        conn = await get_redis_conn()
        cache = await conn.execute('GET', f'{args[0]}:{args[1]}')
        if cache:
            so = kwargs.get('so')
            return await response_from_cache(cache, so)
        else:
            return await func(*args, **kwargs)
    return wrapper


async def store_into_redis(data):
    conn = await get_redis_conn()
    token = data['token']
    sequence = data['data']
    await conn.execute('SET', token, json.dumps(sequence))


async def check_request(request_data):
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
                'message': 'from must be greater than 0 and to must be smaller than 354224848179263100000'
            })
            return False, ERROR_MSG
    elif _type == 'by_pos':
        if not(_from < _to and _from < max_pos and _from >= min_pos and _to > min_pos and _to <= max_pos):
            ERROR_MSG = json.dumps({
                'type': 'error',
                'message': 'from must be greater than 0 and to must be smaller than 100'
            })
            return False, ERROR_MSG
    return True, None


async def websocket_handler(request):
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
                        await fib_handler_by_pos(parsed_data.get('from'), parsed_data.get('to'), so=ws)
                    elif 'by_val' == parsed_data.get('type'):
                        await fib_handler_by_val(parsed_data.get('from'), parsed_data.get('to'), max=config.get('fibonacci').get('max_val'), so=ws)
            else:
                await ws.send_str(msg.data + '/answer')
    return ws


async def arange(starts, ends, step=1):
    for i in range(starts, ends, step):
        yield i


@cache_lookup_by_pos
async def fib_handler_by_pos(pos_from, pos_to, so):
    sequence = []
    async for pos in arange(pos_from, pos_to+1):
        msg = json.dumps({'type': 'item', 'pos': pos, 'val': fib(pos)})
        await so.send_str(msg)
        sequence.append(msg)
    result = {'token': f'{pos_from}:{pos_to}', 'data': sequence}
    await store_into_redis(result)
    await so.send_str(json.dumps({'type': 'info', 'code': 'EOS', 'message': 'End of sequence'}))


@cache_lookup_by_val
async def fib_handler_by_val(*args, **kwargs):
    await fib_handler(*args, **kwargs)


async def fib_handler(lb, rb, d1=0, d2=1, pos=0, max=None, so=None, sequence=None):
    if sequence is None:
        sequence = []
    r = d1 + d2
    if r >= rb or max and r >= max:
        await so.send_str(json.dumps({'type': 'info', 'code': 'EOS', 'message': 'End of sequence'}))
        result = {'token': f'{lb}:{rb}', 'data': sequence}
        await store_into_redis(result)
    elif lb <= r and r < rb:
        if d1 == 0 and d2 == 1:
            await so.send_str(json.dumps({'type': 'item', 'pos': pos, 'val': d1}))
            sequence.append(json.dumps({'type': 'item', 'pos': pos, 'val': d1}))
            pos += 1
            await so.send_str(json.dumps({'type': 'item', 'pos': pos, 'val': d2}))
            sequence.append(json.dumps({'type': 'item', 'pos': pos, 'val': d1}))
            pos += 1
        msg = json.dumps({'type': 'item', 'pos': pos, 'val': r})
        sequence.append(msg)
        await so.send_str(msg)
    await fib_handler(lb, rb, d2, r, pos + 1, max=max, so=so, sequence=sequence)


def main():
    loop = asyncio.get_event_loop()
    app = aiohttp.web.Application(loop=loop)
    app['config'] = config
    app.router.add_route('GET', '/fibo', websocket_handler)
    aiohttp.web.run_app(app, host=app['config'].get('host'), port=app['config'].get('port'))


if __name__ == '__main__':
    main()
