import { PrismaClient } from "@prisma/client";
import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";

// Insights read from the analytics replica with a role that can only SELECT.
export const readonlyPool = new Pool({
  connectionString: process.env.ANALYTICS_DATABASE_URL ?? "postgres://insights@analytics.example.com/support",
  statement_timeout: 5_000,
});

export const analytics = drizzle(readonlyPool);

export const prisma = new PrismaClient();
