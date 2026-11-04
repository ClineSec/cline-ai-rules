import grpc
from a2a.server.request_handlers import DefaultRequestHandler, GrpcHandler
from a2a.types import a2a_pb2_grpc

from planner.wiring import handler

GRPC_ADDR = "[::]:50051"


async def serve_grpc(port: int = 50051) -> None:
    server = grpc.aio.server()
    a2a_pb2_grpc.add_A2AServiceServicer_to_server(GrpcHandler(handler), server)
    # ruleid: a2a-server-without-auth
    server.add_insecure_port(f"[::]:{port}")
    # ruleid: a2a-server-without-auth
    server.add_insecure_port(GRPC_ADDR)
    # ok: a2a-server-without-auth
    server.add_insecure_port(f"127.0.0.1:{port}")
    # ok: a2a-server-without-auth
    server.add_insecure_port("localhost:50052")
    await server.start()
