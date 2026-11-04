import * as grpc from "@grpc/grpc-js";
import { DefaultRequestHandler, InMemoryTaskStore } from "@a2a-js/sdk/server";
import { A2AService, UserBuilder, grpcService } from "@a2a-js/sdk/server/grpc";
import { RecipeExecutor } from "./executor.js";
import { recipeCard } from "./card.js";

const requestHandler = new DefaultRequestHandler(recipeCard, new InMemoryTaskStore(), new RecipeExecutor());
const server = new grpc.Server();
// ruleid: a2a-server-without-auth-ts
server.addService(A2AService, grpcService({ requestHandler, userBuilder: UserBuilder.noAuthentication }));
server.bindAsync("0.0.0.0:50051", grpc.ServerCredentials.createInsecure(), () => {});
