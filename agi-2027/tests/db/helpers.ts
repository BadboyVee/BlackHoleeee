import { randomUUID } from "node:crypto";
import { Client } from "pg";
import { inject } from "vitest";

/** A connection as the database owner. Use asUser/asAnon to act as a real caller. */
export async function connect() {
  const client = new Client({ connectionString: inject("databaseUrl") });
  // The run's teardown drops the database with force; don't crash on that.
  client.on("error", () => {});
  await client.connect();
  return client;
}

/** Signs up a user the way Supabase Auth does: a row in auth.users. */
export async function createUser(
  client: Client,
  { email = `${randomUUID()}@example.com`, meta = {} }: { email?: string; meta?: Record<string, unknown> } = {},
) {
  const { rows } = await client.query<{ id: string }>(
    "insert into auth.users (email, raw_user_meta_data) values ($1, $2) returning id",
    [email, JSON.stringify(meta)],
  );
  return rows[0].id;
}

/** Sets a user's role or status directly, as the admin functions will. */
export async function setProfile(
  client: Client,
  userId: string,
  values: { role?: string; status?: string },
) {
  await client.query(
    "update public.profiles set role = coalesce($2::public.user_role, role), status = coalesce($3::public.account_status, status) where id = $1",
    [userId, values.role ?? null, values.status ?? null],
  );
}

/**
 * Runs fn as a signed-in user, exactly as a request through the Supabase API
 * would: the authenticated role with the user's id in the JWT claims. Always
 * rolls back, so tests never leak changes into each other.
 */
export async function asUser<T>(client: Client, userId: string, fn: () => Promise<T>) {
  return asRole(client, "authenticated", { sub: userId, role: "authenticated" }, fn);
}

/** Runs fn as a signed-out visitor (the anon role). Always rolls back. */
export async function asAnon<T>(client: Client, fn: () => Promise<T>) {
  return asRole(client, "anon", { role: "anon" }, fn);
}

/**
 * Runs fn as the app's service client (the Supabase secret key): the
 * service_role role, which skips RLS but still needs grants. Always rolls back.
 */
export async function asService<T>(client: Client, fn: () => Promise<T>) {
  return asRole(client, "service_role", { role: "service_role" }, fn);
}

async function asRole<T>(
  client: Client,
  role: "authenticated" | "anon" | "service_role",
  claims: Record<string, unknown>,
  fn: () => Promise<T>,
) {
  await client.query("begin");
  try {
    await client.query(`set local role ${role}`);
    await client.query("select set_config('request.jwt.claims', $1, true)", [JSON.stringify(claims)]);
    return await fn();
  } finally {
    await client.query("rollback");
  }
}

/** Postgres "insufficient_privilege": the database refused the action. */
export const PERMISSION_DENIED = "42501";
