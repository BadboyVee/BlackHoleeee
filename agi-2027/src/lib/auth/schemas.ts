import { z } from "zod";

/*
 * The sign-in forms' fields: one schema per form, shared by the browser
 * (instant feedback) and the server actions (the check that counts).
 */

export const PASSWORD_MIN = 8;
/** Supabase Auth hashes passwords with bcrypt, which reads at most 72 bytes. */
export const PASSWORD_MAX = 72;
export const NAME_MAX = 80;

const email = z
  .string()
  .trim()
  .max(254, "That email is too long.")
  .pipe(z.email("Enter your email address."))
  .transform((value) => value.toLowerCase());

/** A new password. Never trimmed: spaces count. */
const newPassword = z
  .string()
  .min(PASSWORD_MIN, `Use at least ${PASSWORD_MIN} characters.`)
  .refine((value) => new TextEncoder().encode(value).length <= PASSWORD_MAX, `Use ${PASSWORD_MAX} characters or fewer.`);

export const signInSchema = z.object({
  email,
  password: z.string().min(1, "Enter your password.").max(256, "That password is too long."),
});

export const signUpSchema = z.object({
  name: z.string().trim().min(1, "Tell us your name.").max(NAME_MAX, `Keep it under ${NAME_MAX} characters.`),
  email,
  password: newPassword,
});

export const emailSchema = z.object({ email });

export const newPasswordSchema = z
  .object({ password: newPassword, confirm: z.string() })
  .refine((values) => values.password === values.confirm, { path: ["confirm"], message: "The passwords don't match." });

/** The first message for each field, from zod's issues. */
export function firstIssues(issues: readonly { path: readonly PropertyKey[]; message: string }[]): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const issue of issues) {
    const field = issue.path[0];
    if (typeof field === "string" && !errors[field]) errors[field] = issue.message;
  }
  return errors;
}

export type SignInValues = z.input<typeof signInSchema>;
export type SignUpValues = z.input<typeof signUpSchema>;
export type EmailValues = z.input<typeof emailSchema>;
export type NewPasswordValues = z.input<typeof newPasswordSchema>;

/**
 * What a sign-in form's server action returns (useActionState). `sent` is
 * for the forms whose job is to send an email: the screen changes to "check
 * your inbox".
 */
export type AuthFormState =
  | { status: "idle" }
  | { status: "sent"; email: string }
  | {
      status: "error";
      message: string;
      /** A follow-up the form offers, such as sending the confirmation email again. */
      offer?: "resend_confirmation";
      fieldErrors?: Record<string, string>;
      /** The email typed, so the form keeps it. Never the password. */
      email?: string;
    };
