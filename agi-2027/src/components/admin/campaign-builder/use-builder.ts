"use client";

import { createContext, useContext } from "react";
import { get, useFormContext, useFormState } from "react-hook-form";

import type { DemoCampaign } from "@/lib/campaigns/demo";
import type { CampaignFormInput, CampaignFormValues } from "@/lib/campaigns/schema";
import type { BuilderMode } from "./form-values";

export function useBuilderForm() {
  return useFormContext<CampaignFormInput, unknown, CampaignFormValues>();
}

/** The message for a field path, including errors set on an array as a whole. */
export function useFieldError(name: string): string | undefined {
  const { control } = useBuilderForm();
  const { errors } = useFormState({ control, name: name as never });
  const error = get(errors, name) as { message?: string; root?: { message?: string } } | undefined;
  return error?.message ?? error?.root?.message;
}

export type BuilderContextValue = {
  mode: BuilderMode;
  /** The campaign being edited or duplicated. */
  source?: DemoCampaign;
  /** Editing a campaign that's already out: no publish choice. */
  alreadyDropped: boolean;
  goTo: (step: number) => void;
};

export const BuilderContext = createContext<BuilderContextValue>({
  mode: "new",
  alreadyDropped: false,
  goTo: () => {},
});

export function useBuilder() {
  return useContext(BuilderContext);
}

/** A stable DOM id for a field path. */
export const fieldId = (name: string) => `field-${name.replace(/\./g, "-")}`;
