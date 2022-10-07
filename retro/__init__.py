from prompt_toolkit.shortcuts import input_dialog

from retro.app import start_app
from retro.backend import Backend
from retro.net.client import RPCStoreClient


def start(server=False):
    # Get connection
    if server:
        backend = Backend(
            auth_token=None  # this will be taken from the global ngrok config
        )
        backend.prepare_tunnel()
        backend.start()
        connection_string = backend.connection_string()
    else:
        connection_string = input_dialog(title="Connect to retro", text="Key:").run()

    # Connect client
    client = RPCStoreClient()
    client.connect(connection_string)

    # start app
    start_app(client, connection_string=connection_string)
