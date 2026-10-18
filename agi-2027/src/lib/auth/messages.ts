/*
 * The words people see when signing in goes wrong, and the notes the
 * sign-in page shows after a redirect. No Next.js or Supabase imports, so
 * they're easy to test.
 */

/** Sorts a Supabase Auth error (it carries a `code`) into a message for the person. */
export function authErrorMessage(error: unknown, contactEmail = ""): string {
  const code = typeof error === "object" && error !== null ? (error as { code?: unknown }).code : undefined;
  const email = contactEmail.trim();
  switch (code) {
    case "invalid_credentials":
      return "That email and password don't match. Try again, or reset your password.";
    case "email_not_confirmed":
      return "Confirm your email first. Check your inbox for our link, or send it again.";
    case "user_banned":
      return accountUnavailableMessage(email);
    case "over_request_rate_limit":
    case "over_email_send_rate_limit":
      return TOO_MANY_TRIES;
    case "weak_password":
      return "Pick a stronger password. A longer one, or a few words together, works well.";
    case "same_password":
      return "That's your current password. Pick a new one.";
    case "user_already_exists":
    case "email_exists":
      return "There's already an account with that email. Sign in instead.";
    case "signup_disabled":
    case "email_provider_disabled":
      return email
        ? `New accounts are closed right now. Email us at ${email} and we'll help.`
        : "New accounts are closed right now. Please try again later.";
    case "email_address_invalid":
      return "That email address can't be used. Try another one.";
    case "email_address_not_authorized":
      return email
        ? `We can't send email to that address yet. Email us at ${email} and we'll set you up.`
        : "We can't send email to that address yet.";
    case "otp_expired":
    case "flow_state_expired":
    case "flow_state_not_found":
    case "bad_code_verifier":
      return LINK_EXPIRED;
    case "session_not_found":
    case "session_expired":
    case "refresh_token_not_found":
      return "Your sign-in has expired. Sign in again.";
    default:
      return "Something went wrong on our side. Try again in a minute.";
  }
}

export const TOO_MANY_TRIES = "Too many tries from here. Wait a few minutes, then try again.";
export const LINK_EXPIRED = "That link has expired or was already used. Ask for a new one below.";
export const NOT_CONNECTED = "Accounts aren't connected yet, so this can't go through.";

export function accountUnavailableMessage(contactEmail = ""): string {
  const email = contactEmail.trim();
  return email
    ? `This account isn't active right now. If that's a mistake, email us at ${email}.`
    : "This account isn't active right now. If that's a mistake, get in touch.";
}

/** Notes the sign-in pages show for ?status= and ?error= after a redirect. */
export type PageNote = { tone: "info" | "success" | "error"; text: string };

export function pageNote(params: { status?: string | null; error?: string | null }, contactEmail = ""): PageNote | null {
  switch (params.error) {
    case "link":
      return { tone: "error", text: LINK_EXPIRED };
    case "google":
      return { tone: "error", text: "Signing in with Google didn't finish. Try again." };
    case "auth":
      return { tone: "error", text: "We couldn't sign you in. Try again." };
  }
  switch (params.status) {
    case "signed-out":
      return { tone: "info", text: "You're signed out." };
    case "confirmed":
      return { tone: "success", text: "Your email is confirmed. Sign in to carry on." };
    case "unavailable":
      return { tone: "error", text: accountUnavailableMessage(contactEmail) };
    case "expired":
      return { tone: "error", text: "That reset link has expired or was already used. Ask for a new one." };
  }
  return null;
}
