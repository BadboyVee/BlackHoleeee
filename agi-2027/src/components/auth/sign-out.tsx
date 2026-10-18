"use client";

import { useTransition } from "react";
import { useFormStatus } from "react-dom";
import { LogOut } from "lucide-react";

import { signOut } from "@/app/(auth)/actions";
import { Button } from "@/components/ui/button";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";

function SignOutSubmit() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" variant="ghost" loading={pending}>
      {pending ? null : <LogOut />}
      Log out
    </Button>
  );
}

/** A log out button as a plain form, so it works before the page's JavaScript loads. */
export function SignOutButton() {
  return (
    <form action={signOut}>
      <SignOutSubmit />
    </form>
  );
}

/** "Log out" as an item in an account menu. */
export function SignOutMenuItem() {
  const [pending, startTransition] = useTransition();
  return (
    <DropdownMenuItem
      disabled={pending}
      onSelect={(event) => {
        // Keep the menu open, showing the item as busy, until the redirect lands.
        event.preventDefault();
        startTransition(() => signOut());
      }}
    >
      <LogOut />
      {pending ? "Logging out" : "Log out"}
    </DropdownMenuItem>
  );
}
