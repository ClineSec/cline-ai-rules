import grpc
from a2a.server.request_handlers import GrpcHandler
from a2a.types import a2a_pb2_grpc

from planner.grpc_auth import TokenInterceptor
from planner.wiring import handler


async def serve_grpc() -> None:
    server = grpc.aio.server(interceptors=[TokenInterceptor()])
    a2a_pb2_grpc.add_A2AServiceServicer_to_server(GrpcHandler(handler), server)
    # ok: a2a-server-without-auth
    server.add_insecure_port("[::]:50051")
    await server.start()
