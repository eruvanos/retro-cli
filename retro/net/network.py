import dataclasses
import json
import logging
import socket
from json import JSONEncoder, JSONDecodeError
from threading import Lock
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EnhancedJSONEncoder(JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class Network:
    BUFFER = 2
    ORDER = "big"

    def __init__(self, socket: socket.socket):
        self.socket = socket
        self._lock = Lock()

    def _recv(self) -> str:
        with self._lock:
            raw_length = self.socket.recv(self.BUFFER)
            length = int.from_bytes(raw_length, self.ORDER, signed=False)
            data = self.socket.recv(length)
            return data.decode()

    def _send(self, msg: str):
        with self._lock:
            data = msg.encode()
            length = int.to_bytes(len(data), self.BUFFER, self.ORDER, signed=False)
            self.socket.sendall(length)
            self.socket.sendall(data)

    def recv_json(self) -> Optional[dict]:
        data = self._recv()
        if not data:
            return None

        try:
            return json.loads(data)
        except JSONDecodeError as e:
            logger.exception(f"Could not parse data: {data}")
            return None

    def send_json(self, data: Any):
        self._send(json.dumps(data, cls=EnhancedJSONEncoder))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.socket.close()


class SecureNetwork(Network):
    def __init__(self, socket_: socket.socket, key: str):
        super().__init__(socket_)

        from cryptography.fernet import Fernet

        self.cipher_suite = Fernet(key.encode())

    # --- security layer
    def _recv(self) -> str:
        recv = super()._recv()
        if recv:
            return self.decrypt(recv)
        else:
            return ""

    def _send(self, msg: str):
        super()._send(self.encrypt(msg))

    # --- crypto
    @staticmethod
    def generate_key():
        from cryptography.fernet import Fernet

        return Fernet.generate_key().decode()

    def encrypt(self, text: str):
        return self.cipher_suite.encrypt(text.encode()).decode()

    def decrypt(self, cipher_text: str):
        return self.cipher_suite.decrypt(cipher_text.encode()).decode()
