/*
 * Plain words for what the onboarding database functions refuse. PostgREST
 * passes each Postgres error code through as `code`. No Next.js or Supabase
 * imports, so these are easy to test.
 */

export type DbError = { code?: string; message?: string } | null | undefined;

export type InviteState = "valid" | "revoked" | "expired" | "used_up" | "unknown";

export const FORM_PROBLEM = "Check the highlighted fields.";
export const NOT_CONNECTED = "Accounts aren't connected yet, so this can't be saved.";
const FAILED = "We couldn't save that just now. Try again in a minute.";

/** What the invite page says for a code that can't be used. */
export function inviteStateMessage(state: InviteState): string {
  switch (state) {
    case "valid":
      return "This invite is ready to use.";
    case "revoked":
      return "This invite link has been switched off. Ask whoever sent it for a new one.";
    case "expired":
      return "This invite link has expired. Ask whoever sent it for a new one.";
    case "used_up":
      return "This invite link has been used as many times as it allows. Ask whoever sent it for a new one.";
    case "unknown":
      return "We don't recognise this invite link. Check it was copied in full.";
  }
}

/** The invite's state from redeem_invite's error ("invite_expired" and so on), or null for any other error. */
export function inviteStateFromError(error: DbError): InviteState | null {
  if (error?.code !== "P0410") return null;
  const state = error.message?.replace(/^invite_/, "");
  return state === "revoked" || state === "expired" || state === "used_up" || state === "unknown" ? state : "unknown";
}

export function applicationErrorMessage(error: DbError): { message: string; field?: string } {
  switch (error?.code) {
    case "23505":
      return { message: "That X handle is already on another account. Email us if it's yours.", field: "xHandle" };
    case "P0409":
      return { message: "You've already applied. We'll email you when there's news." };
    case "42501":
      return { message: "This account can't apply. It may already be approved." };
    case "23514":
      return { message: "Something in the form didn't pass our checks. Look it over and try again." };
    default:
      return { message: FAILED };
  }
}

export function reviewErrorMessage(error: DbError): string {
  switch (error?.code) {
    case "P0409":
      return "Someone already decided on this application. The list is up to date now.";
    case "P0002":
      return "That application no longer exists.";
    case "42501":
      return "Only the agency team can review applications.";
    default:
      return FAILED;
  }
}

export function adminOnlyMessage(error: DbError): string {
  return error?.code === "42501" ? "Only the admin can manage invite links." : FAILED;
}

export function profileErrorMessage(error: DbError): string {
  switch (error?.code) {
    case "42501":
      return "Only approved creators can change this.";
    case "23514":
      return "Something in the form didn't pass our checks. Look it over and try again.";
    default:
      return FAILED;
  }
}
