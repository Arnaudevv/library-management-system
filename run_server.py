import asyncio

from server.connection import socket_listener


if __name__ == "__main__":
    asyncio.run(socket_listener())
