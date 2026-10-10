import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { Client } from "pg";
import type { TestProject } from "vitest/node";

declare module "vitest" {
  export interface ProvidedContext {
    databaseUrl: string;
  }
}

const root = path.resolve(import.meta.dirname, "../..");

/**
 * Creates a throwaway database, loads the Supabase stand-in and every migration
 * in order, and drops the database when the run ends.
 */
export default async function setup(project: TestProject) {
  const serverUrl = process.env.TEST_DATABASE_URL;
  if (!serverUrl) {
    throw new Error(
      "Set TEST_DATABASE_URL to a Postgres server you can create databases on, " +
        "for example postgres://postgres:postgres@localhost:5432/postgres",
    );
  }

  const name = `agi_test_${process.pid}_${Date.now()}`;
  const server = new Client({ connectionString: serverUrl });
  await server.connect();
  await server.query(`create database ${name}`);
  await server.end();

  const url = new URL(serverUrl);
  url.pathname = `/${name}`;
  const databaseUrl = url.toString();

  const db = new Client({ connectionString: databaseUrl });
  await db.connect();
  try {
    await db.query(readFileSync(path.join(root, "tests/db/supabase-shim.sql"), "utf8"));
    const migrationsDir = path.join(root, "supabase/migrations");
    for (const file of readdirSync(migrationsDir).filter((f) => f.endsWith(".sql")).sort()) {
      try {
        await db.query(readFileSync(path.join(migrationsDir, file), "utf8"));
      } catch (error) {
        throw new Error(`Migration ${file} failed: ${(error as Error).message}`);
      }
    }
  } finally {
    await db.end();
  }

  project.provide("databaseUrl", databaseUrl);

  return async () => {
    const cleanup = new Client({ connectionString: serverUrl });
    await cleanup.connect();
    await cleanup.query(`drop database if exists ${name} with (force)`);
    await cleanup.end();
  };
}
