import { jwtVerify } from "jose";
import { cookies } from "next/headers";

const SESSION_KEY = new TextEncoder().encode(process.env.SESSION_SECRET ?? "dev-only-not-a-secret");

/** The signed-in agent's workspace, from the session cookie the dashboard sets at login. */
export async function currentWorkspace(): Promise<string> {
  const token = (await cookies()).get("sc_session")?.value;
  if (!token) throw new Response("Unauthorized", { status: 401 });
  const { payload } = await jwtVerify(token, SESSION_KEY);
  return String(payload.workspaceId);
}
