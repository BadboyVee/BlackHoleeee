import type { RoleClaim } from "./routes";

/** The signed-in person, as the account menus show them. Safe to hand to Client Components. */
export type Account = {
  id: string;
  email: string;
  /** Their display name, or the start of their email when they haven't given one. */
  name: string;
  firstName: string;
  initials: string;
  /** From the database, so it's never out of date. "none" when the account isn't active. */
  role: RoleClaim;
  avatarUrl: string | null;
};

/** "ada.lovelace@kled.ai" becomes "ada.lovelace". */
export function nameFromEmail(email: string): string {
  const local = email.split("@")[0]?.trim() ?? "";
  return local || "You";
}

export function displayNameFor(name: string | null | undefined, email: string): string {
  const clean = (name ?? "").replace(/\s+/g, " ").trim();
  return clean || nameFromEmail(email);
}

export function firstNameFor(name: string): string {
  return name.split(" ")[0] ?? name;
}

/** Up to two letters: "Ada Lovelace" is "AL", "ada.lovelace" is "AD". */
export function initialsFor(name: string): string {
  const words = name.split(/[\s._-]+/).filter(Boolean);
  const letters = words.length > 1 ? [words[0][0], words[words.length - 1][0]] : [...(words[0] ?? "?")].slice(0, 2);
  return letters.join("").toUpperCase();
}

/** Builds the account from the profile row and the token's email. */
export function toAccount(
  id: string,
  profile: { role: string; status: string; display_name: string | null; avatar_url: string | null; email: string | null } | null,
  tokenEmail: string | undefined,
): Account {
  const email = profile?.email ?? tokenEmail ?? "";
  const name = displayNameFor(profile?.display_name, email);
  const active = profile?.status === "active";
  return {
    id,
    email,
    name,
    firstName: firstNameFor(name),
    initials: initialsFor(name),
    role: active ? (profile.role as RoleClaim) : "none",
    avatarUrl: profile?.avatar_url ?? null,
  };
}

const ROLE_LABELS: Record<RoleClaim, string> = {
  admin: "Admin",
  team: "Team",
  creator: "Creator",
  applicant: "Applicant",
  none: "Paused",
};

export function roleLabel(role: RoleClaim): string {
  return ROLE_LABELS[role];
}
