"use client";

import { useWatch } from "react-hook-form";
import { Eye, Lock } from "lucide-react";

import { demoClients, type DemoCampaign } from "@/lib/campaigns/demo";
import { amountSchema, type CampaignFormInput } from "@/lib/campaigns/schema";
import { brandInitials } from "../brand-tile";
import { BriefPreview, CreatorCardPreview, type PreviewModel } from "../campaign-preview";
import type { BuilderMode } from "./form-values";
import { audienceReach } from "./steps/payout";
import { useBuilder, useBuilderForm } from "./use-builder";

const validTime = (iso: string) => Boolean(iso) && Number.isFinite(new Date(iso).getTime());

/** The builder's values as creators would see them on the board. */
export function previewFromValues(values: CampaignFormInput, mode: BuilderMode, source?: DemoCampaign): PreviewModel {
  const client = demoClients.find((entry) => entry.id === values.clientId);
  const brand =
    values.clientId === "new"
      ? { name: values.newClient?.name ?? "", initials: brandInitials(values.newClient?.name ?? "") }
      : client
        ? { name: client.name, initials: client.initials, color: client.color }
        : { name: "", initials: "" };
  const { postWindowStart, postWindowEnd } = values.timing;
  const windowOk =
    validTime(postWindowStart) && validTime(postWindowEnd) && new Date(postWindowEnd).getTime() > new Date(postWindowStart).getTime();
  const editingLive = mode === "edit" && source;
  return {
    brand,
    title: values.title ?? "",
    summary: values.summary ?? "",
    platform: values.platform,
    deliverable: values.deliverable,
    payout: amountSchema.safeParse(values.payout.amount).success ? { amount: values.payout.amount.trim(), currency: values.payout.currency } : null,
    customRates: values.tierPayouts.length + values.creatorPayouts.length > 0,
    slots: Number.isFinite(values.slots) ? values.slots : null,
    slotsTaken: editingLive ? source.slotsTaken : 0,
    window: windowOk ? { start: postWindowStart, end: postWindowEnd } : null,
    claimMode: values.claimMode,
    draftRequired: values.draftRequired,
    paidLabelRequired: values.paidLabelRequired,
    // Creators only ever see a campaign once it's live.
    status: editingLive && source.status !== "draft" && source.status !== "scheduled" ? source.status : "live",
    isNew: !editingLive || source.status === "draft" || source.status === "scheduled",
    brief: values.brief,
    angles: values.angles,
    requiredTags: values.requiredTags,
    links: values.links,
    assets: { files: values.assets.files.length, brandKit: Boolean(values.assets.brandKitUrl) },
  };
}

/** The sticky "what creators will see" column, redrawn as the owner types. */
export function LivePreview({ inSheet = false }: { inSheet?: boolean }) {
  const { control } = useBuilderForm();
  const { mode, source } = useBuilder();
  const values = useWatch({ control }) as CampaignFormInput;
  const model = previewFromValues(values, mode, source);
  const reach = audienceReach(values.audience).length;

  return (
    <div className="grid gap-3">
      <div className="flex items-center justify-between gap-3">
        {inSheet ? null : (
          <p className="flex items-center gap-1.5 text-label text-subtle-foreground">
            <Eye className="size-3.5" aria-hidden />
            What creators will see
          </p>
        )}
        <span className="text-xs text-muted-foreground tabular">
          {reach} {reach === 1 ? "creator" : "creators"} in the audience
        </span>
      </div>
      <CreatorCardPreview model={model} />
      <BriefPreview model={model} />
      <p className="flex items-start gap-1.5 text-xs leading-relaxed text-subtle-foreground">
        <Lock className="mt-0.5 size-3 shrink-0" aria-hidden />
        Budget, admin notes and audience rules never reach creators.
      </p>
    </div>
  );
}
