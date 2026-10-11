"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Check, Film, ImagePlus, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { fieldDescribedBy } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import { draftSchema, tagsFound, type CreatorClaim, type DraftValues } from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { cn } from "@/lib/utils";

import { useClaimActions } from "../claim-store";
import { pressed, springArrive, springPop } from "../motion";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const MAX_MEDIA = 4;
const SHORT_FORMS = new Set(["original", "quote", "reply"]);

type Media = { id: string; name: string; kind: "image" | "video"; sizeBytes: number; url?: string };

/** Live check of the required tags, ticking each one off as it appears in the text. */
export function TagCheck({ text, tags }: { text: string; tags: string[] }) {
  if (tags.length === 0) return null;
  const found = tagsFound(text, tags);
  return (
    <ul aria-label="Required tags" className="flex flex-wrap gap-1.5">
      {tags.map((tag) => (
        <li
          key={tag}
          data-tone={found[tag] ? "green" : undefined}
          className={cn(
            "inline-flex h-7 items-center gap-1 rounded-full border px-2.5 font-mono text-xs font-medium transition-colors duration-300",
            found[tag] ? "border-(--tone-fg)/35 bg-(--tone-fg)/10 text-(--tone-fg)" : "text-muted-foreground",
          )}
        >
          <AnimatePresence initial={false} mode="popLayout">
            {found[tag] ? (
              <motion.span key="yes" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }} transition={springPop}>
                <Check className="size-3" strokeWidth={3} />
              </motion.span>
            ) : null}
          </AnimatePresence>
          {tag}
          <span className="sr-only">{found[tag] ? " included" : " missing"}</span>
        </li>
      ))}
    </ul>
  );
}

/** Write the post, attach media, see the required tags tick off, send it for review. */
export function DraftEditor({ campaign, claim }: { campaign: CreatorCampaign; claim: CreatorClaim }) {
  const actions = useClaimActions();
  const inputId = useId();
  const form = useForm<DraftValues>({
    resolver: zodResolver(draftSchema),
    defaultValues: { text: claim.draft?.text ?? "" },
    mode: "onTouched",
  });
  const text = useWatch({ control: form.control, name: "text" }) ?? "";
  const length = text.trim().length;
  const error = form.formState.errors.text?.message;
  const tags = [...campaign.requiredTags.mentions, ...campaign.requiredTags.hashtags, ...campaign.requiredTags.keywords];

  const [media, setMedia] = useState<Media[]>(
    () => claim.draft?.media.map((file, index) => ({ ...file, id: `saved-${index}-${file.name}` })) ?? [],
  );
  const urls = useRef<string[]>([]);
  useEffect(() => {
    const created = urls.current;
    return () => created.forEach((url) => URL.revokeObjectURL(url));
  }, []);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const room = MAX_MEDIA - media.length;
    const added = [...list].slice(0, room).map((file): Media => {
      const url = URL.createObjectURL(file);
      urls.current.push(url);
      return {
        id: `${file.name}-${file.size}-${file.lastModified}`,
        name: file.name,
        kind: file.type.startsWith("video") ? "video" : "image",
        sizeBytes: file.size,
        url,
      };
    });
    if (list.length > room) toast("Up to 4 files", { description: "Keep the ones that show it best." });
    setMedia((current) => [...current, ...added]);
  }

  const submit = form.handleSubmit(async (values) => {
    await wait(600);
    const ok = actions.submitDraft(campaign, {
      text: values.text.trim(),
      media: media.map(({ name, kind, sizeBytes }) => ({ name, kind, sizeBytes })),
    });
    if (ok) toast.success("Draft sent", { description: "The agency will read it and reply here." });
  });

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      <div className="grid gap-2">
        <div className="flex items-baseline justify-between gap-3">
          <label htmlFor={inputId} className="text-sm font-semibold">
            Your draft
          </label>
          <span
            data-tone={SHORT_FORMS.has(campaign.deliverable) && length > 280 ? "amber" : undefined}
            className={cn("text-xs tabular", SHORT_FORMS.has(campaign.deliverable) && length > 280 ? "text-(--tone-fg)" : "text-muted-foreground")}
          >
            {length}
            {SHORT_FORMS.has(campaign.deliverable) ? "/280" : " characters"}
          </span>
        </div>
        <Textarea
          id={inputId}
          rows={6}
          placeholder="Write it the way you'd post it, in your own voice."
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={fieldDescribedBy(inputId, { hint: true, error })}
          {...form.register("text")}
        />
        {error ? (
          <p id={`${inputId}-error`} role="alert" className="text-[13px] text-destructive-text">
            {error}
          </p>
        ) : (
          <p id={`${inputId}-hint`} className="text-[13px] text-pretty text-muted-foreground">
            {SHORT_FORMS.has(campaign.deliverable) && length > 280
              ? "Over 280 characters. Fine with X Premium, or trim it."
              : "Tags light up as you include them."}
          </p>
        )}
        <TagCheck text={text} tags={tags} />
      </div>

      <div className="grid gap-2">
        <p className="text-sm font-semibold">
          Media <span className="font-normal text-muted-foreground">(optional)</span>
        </p>
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
          <AnimatePresence initial={false}>
            {media.map((item) => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.85 }}
                transition={springArrive}
                className="group relative aspect-square overflow-hidden rounded-xl border bg-surface-2"
              >
                {item.url && item.kind === "image" ? (
                  // eslint-disable-next-line @next/next/no-img-element -- a local preview from the file picker
                  <img src={item.url} alt={item.name} className="size-full object-cover" />
                ) : (
                  <div className="flex size-full flex-col items-center justify-center gap-1.5 p-2 text-center">
                    <Film className="size-5 text-muted-foreground" />
                    <span className="line-clamp-2 text-[11px] break-all text-muted-foreground">{item.name}</span>
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => setMedia((current) => current.filter((entry) => entry.id !== item.id))}
                  aria-label={`Remove ${item.name}`}
                  className="absolute top-1 right-1 flex size-8 cursor-pointer items-center justify-center rounded-full bg-black/60 text-white backdrop-blur-sm transition-colors hover:bg-black/75"
                >
                  <X className="size-4" />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
          {media.length < MAX_MEDIA ? (
            <motion.label
              layout
              whileTap={pressed}
              className="flex aspect-square cursor-pointer flex-col items-center justify-center gap-1.5 rounded-xl border-2 border-dashed border-border-strong text-muted-foreground transition-colors focus-within:ring-2 focus-within:ring-ring hover:border-foreground/40 hover:bg-surface-2 hover:text-foreground"
            >
              <ImagePlus className="size-5" />
              <span className="text-xs font-medium">Add</span>
              <input
                type="file"
                accept="image/*,video/*"
                multiple
                className="sr-only"
                onChange={(event) => {
                  addFiles(event.target.files);
                  event.target.value = "";
                }}
              />
            </motion.label>
          ) : null}
        </div>
        <p className="text-xs text-muted-foreground">In this preview, files stay on your device.</p>
      </div>

      <Button type="submit" variant="brand" size="xl" loading={form.formState.isSubmitting} className="w-full sm:w-auto sm:self-start">
        {form.formState.isSubmitting ? "Sending" : claim.status === "changes_requested" ? "Send updated draft" : "Send draft"}
      </Button>
    </form>
  );
}
