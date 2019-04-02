import json
import aiohttp

class FibClient(object):
    def __init__(self, host, port, path):
        self.endpoint = f'ws://{host}:{port}/{path}'
        self.session = aiohttp.ClientSession()

    def _prepare_message(self, _from, _to, _type):
        return json.dumps({
            "action": "count",
            "from": _from,
            "to": _to,
            "type": _type,
        })

    async def make_request(self, lhv, rhv, _type):
        message = self._prepare_message(lhv, rhv, _type)
        response = []
        async with self.session.ws_connect(self.endpoint) as web_socket:
            await web_socket.send_str(message)
            while not web_socket.closed:
                _resp = await web_socket.receive()
                if web_socket.closed and web_socket.close_code == 1000:
                    break
                _resp = json.loads(_resp.data)
                if _resp.get('type') == 'info' and _resp.get('code') == 'EOS':
                    break
                response.append(_resp)
        return response
