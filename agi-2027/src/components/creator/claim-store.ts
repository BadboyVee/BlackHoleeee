"use client";

import { useMemo, useSyncExternalStore } from "react";

import {
  applyDeadlines,
  canMoveClaim,
  type ClaimActor,
  type ClaimDraft,
  type ClaimProof,
  type CreatorClaim,
} from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import type { ClaimStatus } from "@/lib/statuses";

import { useCreatorDemo } from "./creator-data";
import { useNow } from "./hooks";

/*
 * The demo's claims, kept in this browser until real claiming arrives in
 * Milestone 6. It starts from the seed claims the layout sends, saves every
 * change to localStorage so a refresh keeps it, and tells every open page (and
 * other tabs) when something changes. Each move goes through canMoveClaim, the
 * same rules the database will enforce.
 */

export const CLAIMS_STORAGE_KEY = "agi-demo-claims";
const CHANGE_EVENT = "agi:demo-claims";

type StoredClaims = { version: 1; claims: CreatorClaim[] };

/** Used when storage is blocked (private mode): changes last until the page closes. */
let memory: CreatorClaim[] | null = null;
let cache: { raw: string | null; seed: readonly CreatorClaim[]; claims: readonly CreatorClaim[] } | null = null;

function readRaw(): string | null | undefined {
  try {
    return window.localStorage.getItem(CLAIMS_STORAGE_KEY);
  } catch {
    return undefined;
  }
}

function parse(raw: string): CreatorClaim[] | null {
  try {
    const value = JSON.parse(raw) as Partial<StoredClaims> | null;
    if (!value || value.version !== 1 || !Array.isArray(value.claims)) return null;
    return value.claims.filter(
      (claim) =>
        claim &&
        typeof claim.campaignId === "string" &&
        typeof claim.status === "string" &&
        Array.isArray(claim.events) &&
        claim.payout !== undefined,
    );
  } catch {
    return null;
  }
}

function snapshot(seed: readonly CreatorClaim[]): readonly CreatorClaim[] {
  const raw = readRaw();
  if (raw === undefined) return memory ?? seed;
  if (cache && cache.raw === raw && cache.seed === seed) return cache.claims;
  const claims = (raw ? parse(raw) : null) ?? seed;
  cache = { raw, seed, claims };
  return claims;
}

function subscribe(onChange: () => void) {
  const onStorage = (event: StorageEvent) => {
    if (event.key === null || event.key === CLAIMS_STORAGE_KEY) onChange();
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(CHANGE_EVENT, onChange);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(CHANGE_EVENT, onChange);
  };
}

function write(claims: CreatorClaim[]) {
  memory = claims;
  try {
    window.localStorage.setItem(CLAIMS_STORAGE_KEY, JSON.stringify({ version: 1, claims } satisfies StoredClaims));
  } catch {
    // Storage blocked: keep it in memory for this page.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

/**
 * Every claim the demo creator has: saved state first, seed otherwise, with
 * the deadline rules applied (no proof by the deadline means expired).
 */
export function useClaims(): readonly CreatorClaim[] {
  const { claims: seed, campaigns } = useCreatorDemo();
  const stored = useSyncExternalStore(
    subscribe,
    () => snapshot(seed),
    () => seed,
  );
  const now = useNow(60_000);
  return useMemo(() => {
    if (now === null) return stored;
    const timing = new Map(campaigns.map((campaign) => [campaign.id, campaign.timing]));
    return stored.map((claim) => {
      const t = timing.get(claim.campaignId);
      return t ? applyDeadlines(claim, t, now) : claim;
    });
  }, [stored, campaigns, now]);
}

export function useClaim(campaignId: string): CreatorClaim | undefined {
  return useClaims().find((claim) => claim.campaignId === campaignId);
}

/** The claim this campaign started with in the demo data (already counted in its slots). */
export function useSeedClaim(campaignId: string): CreatorClaim | undefined {
  return useCreatorDemo().claims.find((claim) => claim.campaignId === campaignId);
}

/** A stable, made-up payment reference for the demo: a transaction hash for stablecoins, a bank reference otherwise. */
export function demoPaymentReference(campaignId: string, currency: string): string {
  let hash = 0x811c9dc5;
  let hex = "";
  for (let round = 0; hex.length < 40; round += 1) {
    for (const char of `${campaignId}:${round}`) {
      hash ^= char.charCodeAt(0);
      hash = Math.imul(hash, 0x01000193) >>> 0;
    }
    hex += hash.toString(16).padStart(8, "0");
  }
  return currency.startsWith("USD") && currency !== "USD"
    ? `0x${hex.slice(0, 40)}`
    : `BNK-${hex.slice(0, 4).toUpperCase()}-${parseInt(hex.slice(4, 8), 16) % 10_000}`;
}

/** The angle a new claim gets: spread evenly by creator, the same every time. */
export function assignAngle(angles: readonly string[], key: string): string | undefined {
  if (angles.length === 0) return undefined;
  let sum = 0;
  for (const char of key) sum = (sum * 31 + char.charCodeAt(0)) >>> 0;
  return angles[sum % angles.length];
}

function createActions(seed: readonly CreatorClaim[]) {
  const stamp = () => new Date().toISOString();
  const current = () => [...snapshot(seed)];
  const find = (campaignId: string) => current().find((claim) => claim.campaignId === campaignId);

  function save(next: CreatorClaim) {
    const list = current();
    const index = list.findIndex((claim) => claim.campaignId === next.campaignId);
    if (index >= 0) list[index] = next;
    else list.push(next);
    write(list);
  }

  function move(
    campaign: CreatorCampaign,
    to: ClaimStatus,
    by: ClaimActor,
    { patch = {}, note }: { patch?: Partial<CreatorClaim>; note?: string } = {},
  ): boolean {
    const claim = find(campaign.id);
    if (!claim || !canMoveClaim(claim.status, to, { draftRequired: campaign.draftRequired })) return false;
    save({
      ...claim,
      ...patch,
      status: to,
      events: [...claim.events, { status: to, by, at: stamp(), ...(note ? { note } : {}) }],
    });
    return true;
  }

  return {
    /** Instant mode: the slot is yours straight away. */
    claim(campaign: CreatorCampaign, creatorId: string): boolean {
      if (find(campaign.id)) return false;
      save({
        campaignId: campaign.id,
        status: "claimed",
        payout: campaign.payout,
        angle: assignAngle(campaign.angles, `${creatorId}:${campaign.id}`),
        events: [{ status: "claimed", by: "you", at: stamp() }],
      });
      return true;
    },
    /** Apply mode: a request with a note. It doesn't hold a slot. */
    request(campaign: CreatorCampaign, note: string): boolean {
      if (find(campaign.id)) return false;
      save({
        campaignId: campaign.id,
        status: "requested",
        payout: campaign.payout,
        note,
        events: [{ status: "requested", by: "you", at: stamp(), note }],
      });
      return true;
    },
    submitDraft(campaign: CreatorCampaign, draft: Omit<ClaimDraft, "submittedAt">) {
      return move(campaign, "draft_submitted", "you", {
        patch: { draft: { ...draft, submittedAt: stamp() }, feedback: undefined },
      });
    },
    submitProof(campaign: CreatorCampaign, proof: Omit<ClaimProof, "submittedAt">) {
      return move(campaign, "proof_submitted", "you", {
        patch: { proof: { ...proof, submittedAt: stamp() }, feedback: undefined },
      });
    },
    drop(campaign: CreatorCampaign) {
      const claim = find(campaign.id);
      return move(campaign, "cancelled", "you", {
        note: claim?.status === "requested" ? "You withdrew your request." : "You dropped this claim. The slot reopened.",
      });
    },

    /* The agency's side, for the preview's "Simulate agency review" only. */
    accept(campaign: CreatorCampaign, creatorId: string) {
      return move(campaign, "claimed", "agency", {
        patch: { angle: assignAngle(campaign.angles, `${creatorId}:${campaign.id}`) },
        note: "A slot is yours.",
      });
    },
    decline(campaign: CreatorCampaign) {
      const note = "The agency went with other creators this time.";
      return move(campaign, "cancelled", "agency", { patch: { feedback: note }, note });
    },
    approveDraft(campaign: CreatorCampaign) {
      return move(campaign, "draft_approved", "agency", { note: "Post it inside your window." });
    },
    requestChanges(campaign: CreatorCampaign, note: string) {
      return move(campaign, "changes_requested", "agency", { patch: { feedback: note }, note });
    },
    approveProof(campaign: CreatorCampaign) {
      return move(campaign, "approved", "agency", { note: "Your earning is now Unpaid." });
    },
    rejectProof(campaign: CreatorCampaign, note: string) {
      return move(campaign, "rejected", "agency", { patch: { feedback: note }, note });
    },
    markPaid(campaign: CreatorCampaign) {
      const reference = demoPaymentReference(campaign.id, campaign.payout.currency);
      return move(campaign, "paid", "agency", {
        patch: { paidReference: reference, paidAt: stamp() },
        note: `Reference ${reference}.`,
      });
    },
  };
}

export type ClaimActions = ReturnType<typeof createActions>;

export function useClaimActions(): ClaimActions {
  const { claims: seed } = useCreatorDemo();
  return useMemo(() => createActions(seed), [seed]);
}

/** Puts the demo back to how it started, in every open tab. */
export function resetDemoClaims() {
  memory = null;
  cache = null;
  try {
    window.localStorage.removeItem(CLAIMS_STORAGE_KEY);
  } catch {
    // Nothing saved anyway.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}
