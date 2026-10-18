import { describe, expect, it } from "vitest";

import { displayNameFor, initialsFor, nameFromEmail, roleLabel, toAccount } from "@/lib/auth/account-display";
import { accountUnavailableMessage, authErrorMessage, LINK_EXPIRED, pageNote, TOO_MANY_TRIES } from "@/lib/auth/messages";
import { emailSchema, newPasswordSchema, PASSWORD_MAX, PASSWORD_MIN, signInSchema, signUpSchema } from "@/lib/auth/schemas";

const DASHES = /[–—]/;

function firstError(result: { success: boolean; error?: { issues: { path: PropertyKey[]; message: string }[] } }, field: string) {
  return result.error?.issues.find((issue) => issue.path[0] === field)?.message;
}

describe("auth schemas", () => {
  it("cleans up the email: trimmed and lower case", () => {
    expect(signInSchema.parse({ email: "  Ada@Kled.AI ", password: "x" })).toEqual({ email: "ada@kled.ai", password: "x" });
    expect(emailSchema.parse({ email: "ADA@kled.ai" }).email).toBe("ada@kled.ai");
  });

  it("asks for a real email and a password to sign in", () => {
    expect(firstError(signInSchema.safeParse({ email: "ada", password: "x" }), "email")).toBe("Enter your email address.");
    expect(firstError(signInSchema.safeParse({ email: "ada@kled.ai", password: "" }), "password")).toBe("Enter your password.");
  });

  it("needs a name and a long enough password to sign up, and never trims the password", () => {
    expect(firstError(signUpSchema.safeParse({ name: " ", email: "ada@kled.ai", password: "longenough" }), "name")).toBe(
      "Tell us your name.",
    );
    expect(firstError(signUpSchema.safeParse({ name: "Ada", email: "ada@kled.ai", password: "short" }), "password")).toBe(
      `Use at least ${PASSWORD_MIN} characters.`,
    );
    expect(signUpSchema.parse({ name: " Ada ", email: "ada@kled.ai", password: "  spaced  " })).toEqual({
      name: "Ada",
      email: "ada@kled.ai",
      password: "  spaced  ",
    });
  });

  it("counts the password limit in bytes, as bcrypt does", () => {
    expect(signUpSchema.safeParse({ name: "Ada", email: "ada@kled.ai", password: "a".repeat(PASSWORD_MAX) }).success).toBe(true);
    // 37 two-byte letters are 74 bytes, over the limit, though only 37 characters.
    expect(firstError(signUpSchema.safeParse({ name: "Ada", email: "ada@kled.ai", password: "é".repeat(37) }), "password")).toBe(
      `Use ${PASSWORD_MAX} characters or fewer.`,
    );
  });

  it("makes sure both new passwords match", () => {
    expect(newPasswordSchema.safeParse({ password: "longenough", confirm: "longenough" }).success).toBe(true);
    expect(firstError(newPasswordSchema.safeParse({ password: "longenough", confirm: "different" }), "confirm")).toBe(
      "The passwords don't match.",
    );
  });
});

describe("authErrorMessage", () => {
  it("explains the common sign-in problems in plain words", () => {
    expect(authErrorMessage({ code: "invalid_credentials" })).toMatch(/don't match/);
    expect(authErrorMessage({ code: "email_not_confirmed" })).toMatch(/Confirm your email first/);
    expect(authErrorMessage({ code: "over_request_rate_limit" })).toBe(TOO_MANY_TRIES);
    expect(authErrorMessage({ code: "over_email_send_rate_limit" })).toBe(TOO_MANY_TRIES);
    expect(authErrorMessage({ code: "otp_expired" })).toBe(LINK_EXPIRED);
    expect(authErrorMessage({ code: "same_password" })).toMatch(/current password/);
  });

  it("offers the contact email where a person has to step in", () => {
    expect(authErrorMessage({ code: "user_banned" }, "hi@agi2027.com")).toContain("hi@agi2027.com");
    expect(authErrorMessage({ code: "signup_disabled" }, "hi@agi2027.com")).toContain("hi@agi2027.com");
    expect(authErrorMessage({ code: "signup_disabled" })).not.toContain("@");
  });

  it("falls back to a calm message for anything unknown", () => {
    for (const error of [null, undefined, "boom", {}, { code: "teapot" }, new Error("x")]) {
      expect(authErrorMessage(error)).toBe("Something went wrong on our side. Try again in a minute.");
    }
  });

  it("never uses dashes, per the copy rules", () => {
    const codes = ["invalid_credentials", "email_not_confirmed", "user_banned", "weak_password", "signup_disabled", "email_address_not_authorized", "session_expired", "x"];
    for (const code of codes) expect(authErrorMessage({ code }, "hi@agi2027.com"), code).not.toMatch(DASHES);
  });
});

describe("pageNote", () => {
  it("turns redirect query values into notes", () => {
    expect(pageNote({ status: "signed-out" })).toEqual({ tone: "info", text: "You're signed out." });
    expect(pageNote({ status: "confirmed" })?.tone).toBe("success");
    expect(pageNote({ status: "unavailable" }, "hi@agi2027.com")).toEqual({
      tone: "error",
      text: accountUnavailableMessage("hi@agi2027.com"),
    });
    expect(pageNote({ error: "link" })).toEqual({ tone: "error", text: LINK_EXPIRED });
    expect(pageNote({ error: "google" })?.tone).toBe("error");
  });

  it("puts an error before a status, and ignores values it doesn't know", () => {
    expect(pageNote({ status: "signed-out", error: "link" })?.text).toBe(LINK_EXPIRED);
    expect(pageNote({ status: "<script>" })).toBeNull();
    expect(pageNote({})).toBeNull();
  });
});

describe("account display", () => {
  it("names people by their display name, else by their email", () => {
    expect(displayNameFor("  Ada   Lovelace ", "ada@kled.ai")).toBe("Ada Lovelace");
    expect(displayNameFor("", "ada.lovelace@kled.ai")).toBe("ada.lovelace");
    expect(displayNameFor(null, "")).toBe("You");
    expect(nameFromEmail("@kled.ai")).toBe("You");
  });

  it("makes up to two initials", () => {
    expect(initialsFor("Ada Lovelace")).toBe("AL");
    expect(initialsFor("Ada King Lovelace")).toBe("AL");
    expect(initialsFor("ada.lovelace")).toBe("AL");
    expect(initialsFor("Ada")).toBe("AD");
    expect(initialsFor("")).toBe("?");
  });

  it("builds the account from the profile, with no role unless it's active", () => {
    const profile = { role: "creator", status: "active", display_name: "Ada Lovelace", avatar_url: null, email: "ada@kled.ai" };
    expect(toAccount("u1", profile, "other@kled.ai")).toEqual({
      id: "u1",
      email: "ada@kled.ai",
      name: "Ada Lovelace",
      firstName: "Ada",
      initials: "AL",
      role: "creator",
      avatarUrl: null,
    });
    expect(toAccount("u1", { ...profile, status: "suspended" }, undefined).role).toBe("none");
    expect(toAccount("u1", null, "ada@kled.ai")).toMatchObject({ email: "ada@kled.ai", name: "ada", role: "none" });
  });

  it("labels each role", () => {
    expect(roleLabel("admin")).toBe("Admin");
    expect(roleLabel("none")).toBe("Paused");
  });
});
