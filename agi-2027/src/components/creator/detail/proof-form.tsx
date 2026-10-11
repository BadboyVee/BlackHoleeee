"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Check, Circle, FlaskConical, ImagePlus, Info, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { checkProofLink, makeProofSchema, type CreatorClaim, type ProofValues } from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { platformLabel } from "@/lib/campaigns/options";
import { cn } from "@/lib/utils";

import { useClaimActions } from "../claim-store";
import { useCreatorDemo } from "../creator-data";
import { springArrive, springPop } from "../motion";
import { LocalWindow } from "../time";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** A made-up but valid-looking post ID for the preview's example link. */
function examplePostId(seed: string) {
  let value = 7;
  for (const char of seed) value = (value * 31 + char.charCodeAt(0)) % 1_000_000_007;
  return `1975${String(value).padStart(10, "0")}${String(value % 99_999).padStart(5, "0")}`;
}

/**
 * Paste the post link and confirm the label and brief. The link is checked as
 * you type: a real post on the right platform, from your own handle, saved
 * without tracking bits.
 */
export function ProofForm({ campaign, claim, now }: { campaign: CreatorCampaign; claim: CreatorClaim; now: number | null }) {
  const { me } = useCreatorDemo();
  const actions = useClaimActions();
  const urlId = useId();
  const schema = useMemo(() => makeProofSchema({ platform: campaign.platform, handle: me.handle }), [campaign.platform, me.handle]);
  const form = useForm<ProofValues>({
    resolver: zodResolver(schema),
    defaultValues: { url: "", labelUsed: false, briefFollowed: false },
    mode: "onTouched",
  });
  const url = useWatch({ control: form.control, name: "url" }) ?? "";
  const result = checkProofLink(url, { platform: campaign.platform, handle: me.handle });
  const typed = url.trim().length > 0;
  const changed = result.normalized !== null && result.normalized !== url.trim();

  const [shot, setShot] = useState<{ name: string; url: string } | null>(null);
  const created = useRef<string[]>([]);
  useEffect(() => {
    const urls = created.current;
    return () => urls.forEach((value) => URL.revokeObjectURL(value));
  }, []);

  const beforeWindow = now !== null && now < new Date(campaign.timing.postWindowStart).getTime();
  const errors = form.formState.errors;

  const submit = form.handleSubmit(async () => {
    if (!result.ok || !result.normalized) return;
    await wait(600);
    const ok = actions.submitProof(campaign, {
      url: result.normalized,
      handle: result.post?.handle ?? me.handle.replace(/^@/, ""),
      postId: result.post?.postId ?? "",
      screenshotName: shot?.name,
    });
    if (ok) toast.success("Proof sent", { description: "The agency checks it and you'll hear back here." });
  });

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      {beforeWindow ? (
        <p className="flex items-start gap-2.5 rounded-xl bg-surface-2/70 p-3.5 text-[13px] text-pretty text-muted-foreground">
          <Info className="mt-0.5 size-4 shrink-0" />
          <span>
            Your window is <LocalWindow start={campaign.timing.postWindowStart} end={campaign.timing.postWindowEnd} className="font-medium text-foreground" />.
            Post inside it; a post from outside the window gets flagged for the agency.
          </span>
        </p>
      ) : null}

      <div className="grid gap-2">
        <div className="flex items-baseline justify-between gap-3">
          <label htmlFor={urlId} className="text-sm font-semibold">
            Link to your {platformLabel[campaign.platform]} post
          </label>
          {campaign.platform === "x" ? (
            <button
              type="button"
              onClick={() =>
                form.setValue(
                  "url",
                  `https://twitter.com/${me.handle.replace(/^@/, "")}/status/${examplePostId(campaign.id)}?s=20&t=preview`,
                  { shouldValidate: true, shouldTouch: true },
                )
              }
              className="-mr-2 inline-flex h-9 shrink-0 cursor-pointer items-center gap-1.5 rounded-full px-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground"
            >
              <FlaskConical className="size-3.5" />
              Try an example
            </button>
          ) : null}
        </div>
        <Input
          id={urlId}
          type="url"
          inputMode="url"
          autoComplete="off"
          spellCheck={false}
          placeholder={campaign.platform === "x" ? `x.com/${me.handle.replace(/^@/, "")}/status/...` : "https://"}
          aria-invalid={Boolean(errors.url) || undefined}
          aria-describedby={`${urlId}-checks`}
          {...form.register("url")}
        />
        <ul id={`${urlId}-checks`} aria-live="polite" className="flex flex-col gap-1.5 pt-0.5">
          {result.checks.map((check) => {
            const state = !typed ? "idle" : check.ok ? "ok" : "bad";
            return (
              <li
                key={check.id}
                data-tone={state === "ok" ? "green" : state === "bad" ? "red" : undefined}
                className={cn(
                  "flex items-center gap-2 text-[13px] transition-colors duration-300",
                  state === "idle" ? "text-muted-foreground" : "text-(--tone-fg)",
                )}
              >
                <span className="relative inline-grid size-4 shrink-0 [&>*]:[grid-area:1/1]">
                  <AnimatePresence initial={false}>
                    <motion.span
                      key={state}
                      initial={{ scale: 0.3, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.3, opacity: 0 }}
                      transition={springPop}
                      className="flex items-center justify-center"
                    >
                      {state === "ok" ? (
                        <Check className="size-4" strokeWidth={3} />
                      ) : state === "bad" ? (
                        <X className="size-4" strokeWidth={3} />
                      ) : (
                        <Circle className="size-3.5" />
                      )}
                    </motion.span>
                  </AnimatePresence>
                </span>
                {check.label}
              </li>
            );
          })}
        </ul>
        <AnimatePresence initial={false}>
          {result.ok && changed ? (
            <motion.p
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={springArrive}
              className="overflow-hidden text-xs text-muted-foreground"
            >
              Saved without tracking as <span className="font-mono break-all text-foreground">{result.normalized?.replace("https://", "")}</span>
            </motion.p>
          ) : null}
        </AnimatePresence>
      </div>

      <fieldset className="grid gap-1">
        <legend className="mb-1.5 text-sm font-semibold">Confirm both</legend>
        {(
          [
            { name: "labelUsed", label: "I used the paid partnership label", hint: "On X, it's the “Paid partnership” switch when you post." },
            { name: "briefFollowed", label: "I followed the brief", hint: "Tags, link and key message, posted inside my window." },
          ] as const
        ).map((item) => (
          <Controller
            key={item.name}
            control={form.control}
            name={item.name}
            render={({ field, fieldState }) => (
              <label
                className={cn(
                  "flex min-h-14 cursor-pointer items-start gap-3 rounded-xl border px-3.5 py-3 transition-colors",
                  field.value ? "border-foreground/30 bg-surface-2/60" : "hover:bg-surface-2/40",
                  fieldState.error && "border-destructive-text/50",
                )}
              >
                <Checkbox
                  checked={field.value}
                  onCheckedChange={(checked) => field.onChange(checked === true)}
                  onBlur={field.onBlur}
                  ref={field.ref}
                  aria-invalid={Boolean(fieldState.error) || undefined}
                  className="mt-0.5"
                />
                <span className="min-w-0 text-sm">
                  <span className="block font-medium">{item.label}</span>
                  <span className="block text-[13px] text-pretty text-muted-foreground">{item.hint}</span>
                  {fieldState.error ? (
                    <span role="alert" className="mt-1 block text-[13px] text-destructive-text">
                      {fieldState.error.message}
                    </span>
                  ) : null}
                </span>
              </label>
            )}
          />
        ))}
      </fieldset>

      <div className="grid gap-2">
        <p className="text-sm font-semibold">
          Screenshot <span className="font-normal text-muted-foreground">(optional)</span>
        </p>
        {shot ? (
          <div className="flex items-center gap-3 rounded-xl border bg-surface-2/40 p-2 pr-2">
            {/* eslint-disable-next-line @next/next/no-img-element -- a local preview from the file picker */}
            <img src={shot.url} alt="" className="size-12 rounded-lg object-cover" />
            <span className="min-w-0 flex-1 truncate text-sm">{shot.name}</span>
            <button
              type="button"
              onClick={() => setShot(null)}
              aria-label="Remove screenshot"
              className="flex size-11 cursor-pointer items-center justify-center rounded-full text-muted-foreground hover:bg-surface-2 hover:text-foreground"
            >
              <X className="size-4" />
            </button>
          </div>
        ) : (
          <label className="flex h-12 cursor-pointer items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border-strong text-sm font-medium text-muted-foreground transition-colors focus-within:ring-2 focus-within:ring-ring hover:border-foreground/40 hover:bg-surface-2 hover:text-foreground">
            <ImagePlus className="size-4" />
            Add a screenshot
            <input
              type="file"
              accept="image/*"
              className="sr-only"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) {
                  const preview = URL.createObjectURL(file);
                  created.current.push(preview);
                  setShot({ name: file.name, url: preview });
                }
                event.target.value = "";
              }}
            />
          </label>
        )}
      </div>

      <Button type="submit" variant="brand" size="xl" loading={form.formState.isSubmitting} className="w-full sm:w-auto sm:self-start">
        {form.formState.isSubmitting ? "Sending" : claim.status === "rejected" ? "Send the fixed link" : "Send proof"}
      </Button>
    </form>
  );
}
