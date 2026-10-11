"use client";

import { toast } from "sonner";

export const PREVIEW_NOTE = "Preview only. Saving arrives in Milestone 5.";

/**
 * Every action that would write data says so instead of pretending. The
 * description says what the action will do once it's real.
 */
export function previewOnly(whatItWillDo?: string) {
  toast(PREVIEW_NOTE, whatItWillDo ? { description: whatItWillDo } : undefined);
}
