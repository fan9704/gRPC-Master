from api import api_pb2
from api import api_pb2_grpc


def grpc_hook(server):
    api_pb2_grpc.add_APIServicer_to_server(APIServicer(), server)


class APIServicer(api_pb2_grpc.APIServicer):
    def GetPage(self, request, context):
        response = api_pb2.PageResponse(title="Demo object")
        return response
