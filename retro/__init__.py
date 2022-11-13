from typing import Optional

from prompt_toolkit.shortcuts import input_dialog

from retro.app import start_app
from retro.backend import Backend
from retro.net.client import RPCStoreClient


def start_server(blocking=False) -> Optional[str]:
    """
    Start the backend

    :param blocking: Starts Backend and blocks. This is for server-only mode.
    :return: Connection string if blocking==False
    """
    backend = Backend(
        auth_token=None  # this will be taken from the global ngrok config
    )
    if blocking:
        backend.run()
        return
    else:
        backend.prepare_tunnel()  # prepare tunnel, so we can return connection_string without raise condition
        backend.start()
        return backend.connection_string()


def start(args):
    if args.server_only:
        # Only Server mode
        start_server(blocking=True)
        return
    elif args.server:
        # Server and App mode
        connection_string = start_server(False)
    else:
        # App mode
        connection_string = input_dialog(title="Connect to retro", text="Key:").run()

    # Connect client
    client = RPCStoreClient()
    client.connect(connection_string)

    # start app
    start_app(client, connection_string=connection_string)
