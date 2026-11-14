import socket

from server.settings import HOST, PORT
from server.protocol.request_reader import Request, read_request
from server.protocol.response_builder import Response, StatusCode, build_response
from server.router import Router
from server.error_manager import ErrorManager
from server.static_files import serve_static

LISTEN_BACKLOG = 5

router = Router.create_default()

def handle_connection(conn: socket.socket, addr: tuple[str, int]):
    """Handle one client request and send one HTTP-like response back."""
    try:
        request: Request = read_request(conn)
        
        print(
            f"[REQUEST] {addr[0]}:{addr[1]} "
            f"{request.method} {request.path}",
            flush=True,
        )
        
        response = serve_static(request.path, request.method)
        
        if response is None:
            response = Response(status=StatusCode.OK, body=router.handle(request))

        print(
            f"[RESPONSE] {request.method} {request.path} "
            f"{conn.getpeername()[0]}:{conn.getpeername()[1]} -> "
            f"{conn.getsockname()[0]}:{conn.getsockname()[1]} ",
            flush=True,
        )
        
        conn.sendall(build_response(response))
    except Exception as error:
        response = ErrorManager.handle(error)
        conn.sendall(build_response(response))
    



def socket_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT)) #127.0.0.1:8000
        server_socket.listen(LISTEN_BACKLOG)
        server_socket.settimeout(1)
        print(f"🚀 Server is running at http://{HOST}:{PORT}. Open this URL in your web browser to connect a client.")
        
        while True:
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                continue
            with conn:
                handle_connection(conn, addr)
                


