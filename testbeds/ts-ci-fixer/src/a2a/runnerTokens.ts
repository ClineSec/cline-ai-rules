import { createHash, timingSafeEqual } from "node:crypto";
import type { NextFunction, Request, Response } from "express";

// Self-hosted runners get a per-runner token at registration; only its hash is stored here.
const RUNNER_TOKEN_HASHES = (process.env.CI_FIXER_RUNNER_TOKEN_HASHES ?? "").split(",").filter(Boolean);

function sha256(value: string): Buffer {
  return createHash("sha256").update(value).digest();
}

export function verifyRunnerToken(req: Request, res: Response, next: NextFunction): void {
  const presented = sha256(req.header("x-runner-token") ?? "");
  const known = RUNNER_TOKEN_HASHES.some((hex) => timingSafeEqual(presented, Buffer.from(hex, "hex")));
  if (!known) {
    res.status(401).json({ error: "unknown runner" });
    return;
  }
  next();
}
