"use server";

import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

import { authErrorMessage, NOT_CONNECTED, TOO_MANY_TRIES } from "@/lib/auth/messages";
import { destinationFor, safeNextPath } from "@/lib/auth/routes";
import {
  emailSchema,
  firstIssues,
  newPasswordSchema,
  signInSchema,
  signUpSchema,
  type AuthFormState,
} from "@/lib/auth/schemas";
import { authCallbackUrl, currentRole, requestOrigin } from "@/lib/auth/server";
import { hitRateLimit } from "@/lib/rate-limit";
import { clientIp } from "@/lib/request-ip";
import { siteConfig } from "@/lib/site";
import { getSupabaseEnv } from "@/lib/supabase/env";
import { createClient } from "@/lib/supabase/server";

/*
 * Sign in, sign up, password reset and log out. Each action checks its
 * fields with the same schema the form uses, rate limits by connection (and
 * by email address where one is targeted), then asks Supabase Auth. Errors
 * come back as plain words; passwords never come back at all. redirect()
 * throws, so it's always called outside try blocks.
 */

const FIELDS = "Check the highlighted fields.";

function text(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value.slice(0, 1000) : "";
}

function notConnected(email?: string): AuthFormState {
  const contact = siteConfig.contactEmail.trim();
  return {
    status: "error",
    message: contact ? `${NOT_CONNECTED} Email us at ${contact} and we'll help.` : NOT_CONNECTED,
    email,
  };
}

function failed(error: unknown, email: string): AuthFormState {
  return { status: "error", message: authErrorMessage(error, siteConfig.contactEmail), email };
}

async function visitorIp(): Promise<string> {
  return clientIp(await headers());
}

/** Email and password. Lands people where they were going, or on their role's home. */
export async function signIn(_prev: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const typedEmail = text(formData, "email");
  const parsed = signInSchema.safeParse({ email: typedEmail, password: formData.get("password") ?? "" });
  if (!parsed.success) {
    return { status: "error", message: FIELDS, fieldErrors: firstIssues(parsed.error.issues), email: typedEmail };
  }
  const { email, password } = parsed.data;
  if (!getSupabaseEnv()) return notConnected(email);

  const [byIp, byEmail] = await Promise.all([
    hitRateLimit("sign_in_ip", await visitorIp()),
    hitRateLimit("sign_in_email", email),
  ]);
  if (!byIp || !byEmail) return { status: "error", message: TOO_MANY_TRIES, email };

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) {
    const state = failed(error, email);
    return error.code === "email_not_confirmed" && state.status === "error"
      ? { ...state, offer: "resend_confirmation" }
      : state;
  }
  redirect(destinationFor(await currentRole(supabase), text(formData, "next")));
}

/**
 * A new account with email and password. Supabase emails a confirmation
 * link first (when confirmations are on, as they should be), so the form
 * switches to "check your inbox".
 */
export async function signUp(_prev: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const typedEmail = text(formData, "email");
  const parsed = signUpSchema.safeParse({
    name: text(formData, "name"),
    email: typedEmail,
    password: formData.get("password") ?? "",
  });
  if (!parsed.success) {
    return { status: "error", message: FIELDS, fieldErrors: firstIssues(parsed.error.issues), email: typedEmail };
  }
  const { name, email, password } = parsed.data;
  if (!getSupabaseEnv()) return notConnected(email);
  if (!(await hitRateLimit("sign_up_ip", await visitorIp()))) return { status: "error", message: TOO_MANY_TRIES, email };

  const next = safeNextPath(text(formData, "next"));
  const supabase = await createClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: { data: { full_name: name }, emailRedirectTo: authCallbackUrl(await requestOrigin(), "signup", next) },
  });
  if (error) return failed(error, email);
  if (!data.session) return { status: "sent", email };
  // Email confirmations are off for this project, so they're signed in already.
  redirect(destinationFor(await currentRole(supabase), next));
}

/** Google. Hands the browser to Google, which comes back through /auth/callback. Works without JavaScript. */
export async function signInWithGoogle(formData: FormData): Promise<void> {
  if (!getSupabaseEnv()) redirect("/login?error=google");
  const next = safeNextPath(text(formData, "next"));
  const supabase = await createClient();
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: authCallbackUrl(await requestOrigin(), "google", next),
      queryParams: { prompt: "select_account" },
    },
  });
  if (error || !data.url) {
    console.error(`[auth] starting Google sign in failed: ${error?.code ?? "no url"}`);
    redirect("/login?error=google");
  }
  redirect(data.url);
}

/**
 * Sends a reset link. The answer is the same whether or not the address has
 * an account, so nobody can use this to find out who has one.
 */
export async function requestPasswordReset(_prev: AuthFormState, formData: FormData): Promise<AuthFormState> {
  return sendAuthEmail(formData, async (supabase, email, origin) =>
    supabase.auth.resetPasswordForEmail(email, { redirectTo: authCallbackUrl(origin, "recovery", "/reset-password") }),
  );
}

/** Sends the sign-up confirmation link again. */
export async function resendConfirmation(_prev: AuthFormState, formData: FormData): Promise<AuthFormState> {
  return sendAuthEmail(formData, async (supabase, email, origin) =>
    supabase.auth.resend({
      type: "signup",
      email,
      options: { emailRedirectTo: authCallbackUrl(origin, "signup", safeNextPath(text(formData, "next"))) },
    }),
  );
}

async function sendAuthEmail(
  formData: FormData,
  send: (
    supabase: Awaited<ReturnType<typeof createClient>>,
    email: string,
    origin: string,
  ) => Promise<{ error: { code?: string } | null }>,
): Promise<AuthFormState> {
  const typedEmail = text(formData, "email");
  const parsed = emailSchema.safeParse({ email: typedEmail });
  if (!parsed.success) {
    return { status: "error", message: FIELDS, fieldErrors: firstIssues(parsed.error.issues), email: typedEmail };
  }
  const { email } = parsed.data;
  if (!getSupabaseEnv()) return notConnected(email);

  const [byIp, byAddress] = await Promise.all([
    hitRateLimit("auth_email_ip", await visitorIp()),
    hitRateLimit("auth_email_address", email),
  ]);
  if (!byIp || !byAddress) return { status: "error", message: TOO_MANY_TRIES, email };

  const supabase = await createClient();
  const { error } = await send(supabase, email, await requestOrigin());
  if (error) {
    console.error(`[auth] sending an auth email failed: ${error.code ?? "no code"}`);
    return failed(error, email);
  }
  return { status: "sent", email };
}

/** Sets a new password for the signed-in account. A reset link signs people in for exactly this. */
export async function updatePassword(_prev: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const parsed = newPasswordSchema.safeParse({
    password: formData.get("password") ?? "",
    confirm: formData.get("confirm") ?? "",
  });
  if (!parsed.success) return { status: "error", message: FIELDS, fieldErrors: firstIssues(parsed.error.issues) };
  if (!getSupabaseEnv()) return notConnected();

  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  if (!data?.claims?.sub) redirect("/forgot-password?status=expired");

  const { error } = await supabase.auth.updateUser({ password: parsed.data.password });
  if (error) return { status: "error", message: authErrorMessage(error, siteConfig.contactEmail) };
  redirect(destinationFor(await currentRole(supabase), null));
}

/**
 * Logs out on this device. If Supabase can't be reached, the session cookies
 * are cleared by hand, so logging out always works.
 */
/**
 * Logs out on this device. A form can send `next` (a page on this site) so
 * signing in again goes back there, such as the invite they were looking at.
 */
export async function signOut(formData?: FormData): Promise<void> {
  const next = formData ? safeNextPath(text(formData, "next")) : null;
  if (getSupabaseEnv()) {
    const supabase = await createClient();
    const { error } = await supabase.auth.signOut({ scope: "local" });
    if (error) {
      console.error(`[auth] sign out failed, clearing the session cookies: ${error.code ?? "no code"}`);
      const store = await cookies();
      for (const cookie of store.getAll()) {
        if (/^sb-.+-auth-token/.test(cookie.name)) store.delete(cookie.name);
      }
    }
  }
  redirect(next ? `/login?status=signed-out&next=${encodeURIComponent(next)}` : "/login?status=signed-out");
}
