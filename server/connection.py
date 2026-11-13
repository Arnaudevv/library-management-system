import socket

from server.settings import HOST, PORT
from server.protocol.request_reader import Request, read_request
from server.protocol.response_builder import Response, StatusCode, build_response
from server.router import Router
from server.error_manager import ErrorManager

LISTEN_BACKLOG = 5

router = Router.create_default()


def manage_response(request: Request) -> object:
    """Esta funcion ya no la usaremos."""
    pass
    return router.handle(request)


def handle_connection(conn: socket.socket):
    """Handle one client request and send one HTTP-like response back."""
    try:
        request: Request = read_request(conn)
        response = Response(status=StatusCode.OK, body=router.handle(request))
        conn.sendall(build_response(response))
    except Exception as error:
        response = ErrorManager.handle(error)
        conn.sendall(build_response(response))
    



def socket_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(LISTEN_BACKLOG)
        server_socket.settimeout(1)
        print("Listening on %s:%s", HOST, PORT)
        
        while True:
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                continue
            with conn:
                handle_connection(conn)
                


