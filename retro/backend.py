import base64
import logging
import socket
from threading import Thread
from typing import cast, Optional, Dict

from pyngrok import ngrok
from pyngrok.conf import PyngrokConfig
from pyngrok.ngrok import NgrokTunnel

from retro.net.network import Network, SecureNetwork
from retro.persistence import InMemoryStore

logger = logging.getLogger(__name__)


class Backend(Thread):
    port = 8081

    def __init__(self, auth_token: Optional[str]):
        super().__init__(daemon=True)
        self._auth_token = auth_token
        self.__key = SecureNetwork.generate_key()

        self._tunnel: Optional[NgrokTunnel] = None

    def run(self) -> None:
        self.prepare_tunnel()
        self.serve()

    def prepare_tunnel(self):
        if self._tunnel is None:
            self._tunnel = cast(
                NgrokTunnel,
                ngrok.connect(
                    addr=self.port,
                    proto="tcp",
                    pyngrok_config=PyngrokConfig(auth_token=self._auth_token),
                ),
            )

    def serve(self):
        store = RPCStore()

        threads = []
        # Listen for new connections
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            logger.debug(f"Start server on 127.0.0.1:{self.port}")
            s.bind(("127.0.0.1", self.port))
            s.listen()

            while True:
                conn, addr = s.accept()

                logger.debug(f"Handle new connection")
                handler = RPCConnectionHandler(
                    network=SecureNetwork(conn, self.__key), rpc_handler=store
                )
                handler.start()
                threads.append(handler)

    def url(self):
        return self._tunnel.public_url

    def connection_string(self):
        string = f"{self.url()}|{self.__key}"
        return base64.urlsafe_b64encode(string.encode()).decode()


# class EchoConnectionHandler(Thread):
#     def __init__(self, network: Network):
#         super().__init__(daemon=True)
#         self.network = network
#
#     def run(self):
#         with self.network:
#             while data := self.network.recv_json():
#                 print('receive:', data)
#                 self.network.send_json(data)


class RPCHandler:
    def rpc(self, data: Dict) -> Dict:
        raise NotImplementedError()


class RPCConnectionHandler(Thread):
    def __init__(self, network: Network, rpc_handler: RPCHandler):
        super().__init__(daemon=True)
        self.network = network
        self.rpc_handler = rpc_handler

    def run(self):
        with self.network:
            while data := self.network.recv_json():
                logger.debug("request:", data)
                response = self.rpc_handler.rpc(data)
                logger.debug("response:", response)
                self.network.send_json(response)


class RPCStore(RPCHandler):
    def __init__(self):
        self.store = InMemoryStore()

    def rpc(self, data: Dict):
        method_name = data.get("method")
        params = data.get("params", {})

        if not hasattr(self.store, method_name):
            return {"error": {"code": -32601, "message": "Method not found"}}

        method = getattr(self.store, method_name)
        result = method(**params)

        return {"result": result}


if __name__ == "__main__":
    backend = Backend(auth_token=None)
    backend.prepare_tunnel()
    backend.start()
    print("Connection string:", backend.connection_string())
    backend.join()
