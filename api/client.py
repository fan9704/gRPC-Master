import grpc
from typing import Optional

from api import api_pb2, api_pb2_grpc


class APIGrpcClient:
    def __init__(self, address: str = "localhost:50051"):
        self.address: str = address
        self.stub: Optional[api_pb2_grpc.APIStub] = None
        self.channel: Optional[grpc.Channel] = None

    def connect(self) -> None:
        """
        Open connection to server, must be closed manually.

        :return: nothing
        """
        self.channel = grpc.insecure_channel(self.address)
        self.stub = api_pb2_grpc.APIStub(self.channel)

    def close(self) -> None:
        """
        Close currently opened server channel connection.

        :return: nothing
        """
        if self.channel:
            self.channel.close()
            self.channel = None

    def get_page(self):
        response = self.stub.GetPage(api_pb2.PageRequest())
        return response
