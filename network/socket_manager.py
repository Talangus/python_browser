import socket
import ssl

from util.utils import *

class SocketManager:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SocketManager, cls).__new__(cls)
        return cls.instance
    
    def __init__(self):
        self.sockets = {}

    def get_socket(self, host, port):
        name = generate_host_key(host, port)
        if name in self.sockets:
            return self.sockets[name]
        else:
            new_socket = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP
            )
            new_socket.connect((host, port))
            
            self.sockets[name] = new_socket
            return new_socket

    def upgrade_to_https(self, host, port, allow_invalid_cert):
        name = generate_host_key(host, port)
        
        if name not in self.sockets:
            raise CustomError("Upgrade request on non existent socket: " + name)

        socket = self.sockets[name]

        ctx = ssl.create_default_context()
        if allow_invalid_cert:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        try:
            socket = ctx.wrap_socket(socket, server_hostname=host)
        except Exception as https_error:
            print("Error while upgrading to https: " + str(https_error))
            raise https_error

        self.sockets[name] = socket
        return socket

    def close_all(self):
        for name, sock in self.sockets.items():
            sock.close()

    def is_HTTPS_socket(self, host, port):
        socket = self.get_socket(host, port)
        return isinstance(socket, ssl.SSLSocket)
    
    def reset_connection(self, host, port):
        new_socket = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP
        )
        new_socket.connect((host, port))

        name = generate_host_key(host, port)
        self.sockets[name] = new_socket
        
        return new_socket
            
 
socket_manager = SocketManager()    
    

