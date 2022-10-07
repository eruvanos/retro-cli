import base64
import socket
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4

from retro.net.network import SecureNetwork, Network
from retro.persistence import Category, RetroStore, Item


class Client:
    net: Network

    def __init__(self, net: Network = None):
        self.net = net

    def connect(self, connection_string: str):
        raw = base64.urlsafe_b64decode(connection_string.encode()).decode()
        url_str, key = raw.split("|")
        url = urlparse(url_str)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((url.hostname, url.port))

        self.net = SecureNetwork(s, key=key)


class RPCStoreClient(Client, RetroStore):
    def _rpc_call(self, method: str, **params):
        request_id = str(uuid4())

        self.net.send_json(
            {"jsonrpc": "2.0", "method": method, "params": params, "id": request_id}
        )

        response = self.net.recv_json()
        return response.get("result")

    def list(self, category: Optional[str] = None):
        return [Item(**item) for item in self._rpc_call("list", category=category)]

    def add_item(self, text: str, category: str):
        return self._rpc_call("add_item", text=text, category=category)

    def move_item(self, key: int, category: str):
        return self._rpc_call("move_item", key=key, category=category)

    def remove(self, key: int):
        return self._rpc_call("remove", key=key)


if __name__ == "__main__":
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.connect(('127.0.0.1', 80))
    #
    # net = SecureNetwork(s, key='cLkTkhM-sw6y6529JT5KPf1v5ME7fPany4Lo423v7v8=')
    # net.send_json({'hello': 'world'})
    # print(net.recv_json())

    con_str = input("connection string: ")
    client = RPCStoreClient()
    client.connect(con_str)

    response = client.list(Category.GOOD)
    print(response)
