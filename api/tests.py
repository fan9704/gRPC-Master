import socket
import threading

from django.test import SimpleTestCase

from api import api_pb2_grpc


def free_port() -> int:
    """获取闲置的端口号

    Determines a free port using sockets.
    """
    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind(('127.0.0.1', 0))
    free_socket.listen(5)
    port: int = free_socket.getsockname()[1]
    free_socket.close()
    return port


# Create your tests here.
class LiveServerThread(threading.Thread):
    def __init__(self, port=None):
        self.port = port
        self.is_ready = threading.Event()
        self.error = None
        super().__init__()

    def run(self):
        try:
            self.httpd = self._create_server()
            self.is_ready.set()
            self.httpd.start()
            self.httpd.wait_for_termination()
        except Exception as e:
            self.error = e
            self.is_ready.set()

    def _create_server(self):
        import grpc
        from concurrent import futures
        from api.server import APIServicer
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        api_pb2_grpc.add_APIServicer_to_server(APIServicer(), server)
        address = '[::]:{0}'.format(self.port)
        server.add_insecure_port(address)
        return server

    def terminate(self):
        if hasattr(self, 'httpd'):
            # Stop the WSGI server
            self.httpd.shutdown()
            self.httpd.server_close()
        self.join()


class GRPCTestCase(SimpleTestCase):
    server_thread = None
    port = None
    server_thread_class = LiveServerThread

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.port = free_port()
        cls.server_thread = cls._create_server_thread()
        cls.server_thread.daemon = True
        cls.server_thread.start()
        cls.server_thread.is_ready.wait()
        if cls.server_thread.error:
            # Clean up behind ourselves, since tearDownClass won't get called in
            # case of errors.
            cls._tearDownClassInternal()
            raise cls.server_thread.error

    @classmethod
    def _create_server_thread(cls):
        return cls.server_thread_class(
            port=cls.port,
        )

    @classmethod
    def _tearDownClassInternal(cls):
        # There may not be a 'server_thread' attribute if setUpClass() for some
        # reasons has raised an exception.
        if hasattr(cls, 'server_thread'):
            # Terminate the live server's thread
            cls.server_thread.terminate()

            super().tearDownClass()


class TestBaeServer(GRPCTestCase):
    _grpc_client = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from api.client import APIGrpcClient
        cls._grpc_client = APIGrpcClient(address=f"localhost:{cls.port}")
        cls._grpc_client.connect()

    @classmethod
    def tearDownClass(cls):
        cls._grpc_client.close()

    def test_get_page(self):
        result = self._grpc_client.get_page()
        self.assertEqual(result.title, "Demo object")