"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { FormProvider, useForm, useWatch, type FieldErrors, type FieldPath } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { toast } from "sonner";
import { ArrowLeft, ArrowRight, Check, Copy, Eye, History, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { campaignById, clientById, type DemoCampaign } from "@/lib/campaigns/demo";
import { publishMeta } from "@/lib/campaigns/options";
import { makeCampaignSchema, type CampaignFormInput, type CampaignFormValues } from "@/lib/campaigns/schema";
import { campaignStatusMeta } from "@/lib/statuses";
import { AdminPageHeader } from "../admin-page-header";
import { BrandTile } from "../brand-tile";
import { Callout } from "../form-field";
import { Kbd, useIsApple } from "../kbd";
import { springMove } from "../motion";
import { LocalClock, LocalWhen, useInBrowser } from "../time-text";
import {
  campaignToFormInput,
  DRAFT_STORAGE_KEY,
  editStorageKey,
  emptyCampaign,
  errorPaths,
  hasDropped,
  normalizeCampaign,
  stepForPath,
  STEPS,
  type BuilderMode,
} from "./form-values";
import { GuideSheet } from "./guide-sheet";
import { LivePreview } from "./preview-panel";
import { Stepper } from "./stepper";
import { BasicsStep } from "./steps/basics";
import { BriefStep } from "./steps/brief";
import { PayoutStep } from "./steps/payout";
import { RequirementsStep } from "./steps/requirements";
import { ReviewStep } from "./steps/review";
import { TimingStep } from "./steps/timing";
import { BuilderSuccess } from "./success";
import { BuilderContext, type BuilderContextValue } from "./use-builder";

const LAST = STEPS.length - 1;

/* ------------------------------------------------------------ saved drafts */

type SavedDraft = {
  v: 1;
  mode: BuilderMode;
  sourceId: string | null;
  step: number;
  savedAt: string;
  values: CampaignFormInput;
};

function readDraft(key: string): SavedDraft | null {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<SavedDraft>;
    if (parsed?.v !== 1 || !parsed.values || typeof parsed.values !== "object") return null;
    return parsed as SavedDraft;
  } catch {
    return null;
  }
}

function writeDraft(key: string, draft: SavedDraft) {
  try {
    window.localStorage.setItem(key, JSON.stringify(draft));
  } catch {
    // Private mode or a full disk: the form still works, it just won't survive a reload.
  }
}

function clearDraft(key: string) {
  try {
    window.localStorage.removeItem(key);
  } catch {
    // Same as above.
  }
}

const NESTED = ["brief", "links", "requiredTags", "assets", "payout", "audience", "timing", "internal"] as const;

/** Fills anything missing from an older save with fresh values, so every field exists. */
function mergeValues(base: CampaignFormInput, saved: Partial<CampaignFormInput>): CampaignFormInput {
  const merged = { ...base, ...saved } as CampaignFormInput;
  for (const key of NESTED) {
    (merged as Record<string, unknown>)[key] = { ...base[key], ...((saved[key] as object | undefined) ?? {}) };
  }
  return merged;
}

type Seed = { values: CampaignFormInput; step: number; restoredAt: string | null };

function baseValues(mode: BuilderMode, source?: DemoCampaign) {
  if (source && mode !== "new") return campaignToFormInput(source, mode === "edit" ? "edit" : "duplicate");
  return emptyCampaign();
}

function loadSeed(mode: BuilderMode, source: DemoCampaign | undefined, storageKey: string): Seed {
  const base = baseValues(mode, source);
  const saved = readDraft(storageKey);
  if (saved && saved.mode === mode && saved.sourceId === (source?.id ?? null)) {
    return {
      values: mergeValues(base, saved.values),
      step: Math.min(Math.max(0, Math.floor(saved.step) || 0), LAST),
      restoredAt: saved.savedAt,
    };
  }
  return { values: base, step: 0, restoredAt: null };
}

/* ---------------------------------------------------------------- skeleton */

export function BuilderSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading the campaign builder">
      <div className="mb-8 grid gap-2">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-4 w-80 max-w-full" />
      </div>
      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_23rem]">
        <div className="grid gap-5">
          <div className="grid grid-cols-6 gap-2">
            {STEPS.map((step) => (
              <Skeleton key={step.id} className="h-1.5" />
            ))}
          </div>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-56 w-full rounded-lg" />
          <Skeleton className="h-72 w-full rounded-lg" />
        </div>
        <div className="hidden gap-3 xl:grid">
          <Skeleton className="h-64 w-full rounded-2xl" />
          <Skeleton className="h-80 w-full rounded-2xl" />
        </div>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------- builder */

/**
 * The campaign builder: six steps, a live preview of what creators will see,
 * autosave on this device, and validation that takes the owner straight to
 * the step with the problem. It runs only in the browser: it reads the saved
 * draft and shows times in the owner's own time zone.
 */
export function CampaignBuilder({
  mode,
  sourceId,
  openGuide = false,
}: {
  mode: BuilderMode;
  /** The campaign to edit or duplicate. */
  sourceId?: string;
  openGuide?: boolean;
}) {
  const inBrowser = useInBrowser();
  if (!inBrowser) return <BuilderSkeleton />;
  const source = sourceId ? campaignById(sourceId) : undefined;
  const effectiveMode: BuilderMode = mode !== "new" && !source ? "new" : mode;
  return <BuilderLoader mode={effectiveMode} source={source} openGuide={openGuide} missingSource={Boolean(sourceId && !source)} />;
}

function BuilderLoader({
  mode,
  source,
  openGuide,
  missingSource,
}: {
  mode: BuilderMode;
  source?: DemoCampaign;
  openGuide: boolean;
  missingSource: boolean;
}) {
  const storageKey = mode === "edit" && source ? editStorageKey(source.id) : DRAFT_STORAGE_KEY;
  const [seed, setSeed] = useState<Seed>(() => loadSeed(mode, source, storageKey));
  const [generation, setGeneration] = useState(0);

  const restart = useCallback(() => {
    clearDraft(storageKey);
    setSeed({ values: baseValues(mode, source), step: 0, restoredAt: null });
    setGeneration((value) => value + 1);
  }, [mode, source, storageKey]);

  return (
    <BuilderForm
      key={generation}
      mode={mode}
      source={source}
      seed={seed}
      storageKey={storageKey}
      openGuide={openGuide && generation === 0}
      missingSource={missingSource && generation === 0}
      onRestart={restart}
    />
  );
}

function BuilderForm({
  mode,
  source,
  seed,
  storageKey,
  openGuide,
  missingSource,
  onRestart,
}: {
  mode: BuilderMode;
  source?: DemoCampaign;
  seed: Seed;
  storageKey: string;
  openGuide: boolean;
  missingSource: boolean;
  onRestart: () => void;
}) {
  const alreadyDropped = mode === "edit" && source ? hasDropped(source.status) : false;
  const schema = useMemo(() => makeCampaignSchema(undefined, { alreadyDropped }), [alreadyDropped]);
  const methods = useForm<CampaignFormInput, unknown, CampaignFormValues>({
    resolver: zodResolver(schema),
    defaultValues: seed.values,
    mode: "onTouched",
  });
  const reducedMotion = useReducedMotion();
  const apple = useIsApple();

  const [step, setStep] = useState(seed.step);
  const [furthest, setFurthest] = useState(seed.step);
  const [direction, setDirection] = useState(1);
  const [problems, setProblems] = useState<number[]>([]);
  const [done, setDone] = useState<CampaignFormValues | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(seed.restoredAt);
  const [restoredAt, setRestoredAt] = useState(seed.restoredAt);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [seedJson] = useState(() => JSON.stringify(seed.values));

  const topRef = useRef<HTMLDivElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const stepRef = useRef(seed.step);
  const pendingFocus = useRef<string | null>(null);
  const stepChanged = useRef(false);
  const doneRef = useRef(false);

  const publish = useWatch({ control: methods.control, name: "publish" });
  const sourceId = source?.id ?? null;

  // Autosave: half a second after the last change, keep everything on this device.
  useEffect(() => {
    let timer: number | undefined;
    const unsubscribe = methods.subscribe({
      formState: { values: true },
      callback: ({ values }) => {
        window.clearTimeout(timer);
        timer = window.setTimeout(() => {
          if (doneRef.current || JSON.stringify(values) === seedJson) return;
          const at = new Date().toISOString();
          writeDraft(storageKey, { v: 1, mode, sourceId, step: stepRef.current, savedAt: at, values });
          setSavedAt(at);
        }, 500);
      },
    });
    return () => {
      window.clearTimeout(timer);
      unsubscribe();
    };
  }, [methods, storageKey, mode, sourceId, seedJson]);

  useEffect(() => {
    if (missingSource) toast("That campaign wasn't found, so this is a blank one.");
  }, [missingSource]);

  // Cache Components keeps this page around (hidden) after navigating away. If
  // the campaign was finished, come back to a fresh form instead of the
  // success screen.
  useLayoutEffect(
    () => () => {
      if (doneRef.current) onRestart();
    },
    [onRestart],
  );

  function persistStep(target: number) {
    const current = readDraft(storageKey);
    if (current && current.mode === mode && current.sourceId === sourceId) writeDraft(storageKey, { ...current, step: target });
  }

  function goDirect(target: number, focusPath?: string) {
    if (target === stepRef.current) return;
    pendingFocus.current = focusPath ?? null;
    stepChanged.current = true;
    setDirection(target > stepRef.current ? 1 : -1);
    stepRef.current = target;
    setStep(target);
    setFurthest((value) => Math.max(value, target));
    persistStep(target);
    const top = topRef.current;
    if (top && top.getBoundingClientRect().top < 0) {
      top.scrollIntoView({ block: "start", behavior: reducedMotion ? "auto" : "smooth" });
    }
  }

  async function goTo(target: number) {
    const from = stepRef.current;
    if (target === from) return;
    if (target < from) {
      goDirect(target);
      return;
    }
    for (let index = from; index < target; index++) {
      const fields = STEPS[index].fields as unknown as FieldPath<CampaignFormInput>[];
      const ok = await methods.trigger(fields, { shouldFocus: index === from });
      if (!ok) {
        setProblems((value) => [...new Set([...value, index])]);
        if (index !== from) goDirect(index);
        toast.error(`Check ${STEPS[index].title} first`, { description: "The fields that need a look are marked in red." });
        return;
      }
      setProblems((value) => value.filter((entry) => entry !== index));
    }
    goDirect(target);
  }

  function onValid(values: CampaignFormValues) {
    doneRef.current = true;
    clearDraft(storageKey);
    setProblems([]);
    setDone(normalizeCampaign(values));
    window.scrollTo({ top: 0, behavior: reducedMotion ? "auto" : "smooth" });
  }

  function onInvalid(errors: FieldErrors<CampaignFormInput>) {
    const paths = errorPaths(errors);
    const steps = [...new Set(paths.map(stepForPath))].sort((a, b) => a - b);
    setProblems(steps);
    const first = steps[0] ?? 0;
    if (first !== stepRef.current) goDirect(first, paths.find((path) => stepForPath(path) === first));
    toast.error(
      paths.length === 1 ? `One thing to fix in ${STEPS[first].title}` : `${paths.length} things to fix, starting with ${STEPS[first].title}`,
      { description: "Each one is marked next to its field." },
    );
  }

  function primary() {
    if (stepRef.current < LAST) void goTo(stepRef.current + 1);
    else void methods.handleSubmit(onValid, onInvalid)();
  }

  function afterEnter() {
    if (!stepChanged.current) return;
    stepChanged.current = false;
    const path = pendingFocus.current;
    pendingFocus.current = null;
    if (path) {
      try {
        methods.setFocus(path as FieldPath<CampaignFormInput>);
      } catch {
        // Not every path has a focusable field (a list as a whole, say).
      }
      const active = document.activeElement;
      if (active && active !== document.body && topRef.current?.contains(active)) return;
    }
    headingRef.current?.focus({ preventScroll: true });
  }

  const context: BuilderContextValue = { mode, source, alreadyDropped, goTo: (index) => void goTo(index) };
  const finalLabel = alreadyDropped ? "Save changes" : publishMeta[publish ?? "now"].action;
  const client = source ? clientById(source.clientId) : undefined;

  const title = mode === "edit" ? "Edit campaign" : mode === "duplicate" ? "Duplicate campaign" : "New campaign";
  const eyebrow =
    source && mode !== "new" ? (
      <span className="inline-flex min-w-0 items-center gap-2">
        <BrandTile initials={client?.initials ?? "?"} color={client?.color} size="xs" />
        <span className="truncate">
          {mode === "duplicate" ? "Copy of " : ""}
          {source.title}
        </span>
      </span>
    ) : undefined;

  if (done) {
    return (
      <BuilderSuccess
        values={done}
        mode={mode}
        source={source}
        alreadyDropped={alreadyDropped}
        onKeepEditing={() => {
          doneRef.current = false;
          setDone(null);
        }}
        onCreateAnother={() => {
          doneRef.current = false;
          onRestart();
        }}
      />
    );
  }

  return (
    <BuilderContext.Provider value={context}>
      <FormProvider {...methods}>
        <div ref={topRef} className="scroll-mt-20">
          <AdminPageHeader
            title={title}
            eyebrow={eyebrow}
            description="Six short steps. Everything saves on this device as you go."
            actions={
              <>
                <p className="mr-1 hidden items-center gap-1.5 text-xs text-muted-foreground md:flex" aria-live="polite">
                  {savedAt ? (
                    <>
                      <Check className="size-3.5 text-(--tone-green)" data-tone="green" aria-hidden />
                      Saved on this device at <LocalClock value={savedAt} />
                    </>
                  ) : (
                    "Saves on this device as you type"
                  )}
                </p>
                <Button type="button" variant="secondary" size="sm" className="xl:hidden" onClick={() => setPreviewOpen(true)}>
                  <Eye aria-hidden />
                  Preview
                </Button>
                <GuideSheet defaultOpen={openGuide} />
                <Button type="button" variant="ghost" size="sm" className="text-muted-foreground" onClick={() => setConfirmOpen(true)}>
                  <RotateCcw aria-hidden />
                  {mode === "edit" ? "Discard" : "Start over"}
                </Button>
              </>
            }
          />

          <div className="mb-5 grid gap-2.5 empty:hidden">
            {restoredAt ? (
              <Callout
                title="Picked up where you left off"
                action={
                  <Button type="button" variant="ghost" size="sm" onClick={() => setRestoredAt(null)}>
                    Dismiss
                  </Button>
                }
              >
                <History className="mr-1 inline size-3.5 align-[-2px]" aria-hidden />
                Restored from this device, last saved <LocalWhen value={restoredAt} />.
              </Callout>
            ) : null}
            {mode === "duplicate" && source ? (
              <Callout title={`Duplicating ${source.title}`}>
                <span className="inline-flex items-start gap-1">
                  <Copy className="mt-0.5 size-3.5 shrink-0" aria-hidden />
                  The brand, brief, rules, payout and audience are copied. The times are cleared, so pick new ones on the
                  Timing step.
                </span>
              </Callout>
            ) : null}
            {mode === "edit" && source && alreadyDropped ? (
              <Callout title={`Editing a ${campaignStatusMeta[source.status].label.toLowerCase()} campaign`}>
                Creators on it are told the brief changed when you save. What they&apos;re paid stays as it was when they
                claimed.
              </Callout>
            ) : null}
          </div>

          <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_23rem]">
            <form
              noValidate
              aria-labelledby="builder-step-title"
              onSubmit={(event) => {
                event.preventDefault();
                primary();
              }}
              onKeyDown={(event) => {
                if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
                  event.preventDefault();
                  primary();
                }
              }}
              className="min-w-0"
            >
              <Stepper step={step} furthest={furthest} problems={problems} onSelect={(index) => void goTo(index)} />

              <div className="mt-5 mb-5">
                <p className="text-label text-subtle-foreground">
                  Step {step + 1} of {STEPS.length}
                </p>
                <h2
                  id="builder-step-title"
                  ref={headingRef}
                  tabIndex={-1}
                  className="mt-1 text-xl font-semibold tracking-[-0.025em] outline-none"
                >
                  {STEPS[step].title}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">{STEPS[step].description}</p>
              </div>

              <AnimatePresence mode="wait" initial={false} custom={direction}>
                <motion.div
                  key={step}
                  custom={direction}
                  variants={{
                    enter: (dir: number) => ({ opacity: 0, x: dir * 28 }),
                    center: { opacity: 1, x: 0 },
                    exit: (dir: number) => ({ opacity: 0, x: dir * -18, transition: { duration: 0.12 } }),
                  }}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ x: springMove, opacity: { duration: 0.18 } }}
                  onAnimationComplete={(definition) => {
                    if (definition === "center") afterEnter();
                  }}
                >
                  {step === 0 ? <BasicsStep /> : null}
                  {step === 1 ? <BriefStep /> : null}
                  {step === 2 ? <RequirementsStep /> : null}
                  {step === 3 ? <PayoutStep /> : null}
                  {step === 4 ? <TimingStep /> : null}
                  {step === 5 ? <ReviewStep /> : null}
                </motion.div>
              </AnimatePresence>

              <div className="sticky bottom-0 z-20 -mx-4 mt-8 border-t bg-background/90 px-4 pt-3 pb-safe backdrop-blur-xl sm:mx-0 sm:mb-3 sm:rounded-xl sm:border sm:bg-surface/90 sm:px-3 sm:py-2.5 sm:shadow-float">
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => goDirect(step - 1)}
                    disabled={step === 0}
                    className="h-11 sm:h-10"
                  >
                    <ArrowLeft aria-hidden />
                    Back
                  </Button>
                  <p className="hidden flex-1 items-center justify-center gap-1.5 text-xs text-muted-foreground md:flex">
                    <Kbd>{apple ? "⌘" : "Ctrl"}</Kbd>
                    <Kbd>Enter</Kbd>
                    {step < LAST ? "for the next step" : "to finish"}
                  </p>
                  <Button
                    type="submit"
                    variant={step === LAST ? "brand" : "default"}
                    className="ml-auto h-11 min-w-36 sm:h-10"
                  >
                    {step === LAST ? (
                      finalLabel
                    ) : (
                      <>
                        <span>
                          Next<span className="hidden sm:inline">: {STEPS[step + 1].short}</span>
                        </span>
                        <ArrowRight aria-hidden />
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </form>

            <aside aria-label="Preview" className="hidden xl:block">
              <div className="sticky top-20 max-h-[calc(100dvh-6rem)] overflow-y-auto overscroll-contain pr-1 pb-6 [scrollbar-width:thin]">
                <LivePreview />
              </div>
            </aside>
          </div>
        </div>

        <Sheet open={previewOpen} onOpenChange={setPreviewOpen}>
          <SheetContent side="bottom" className="gap-0 xl:hidden">
            <SheetHeader className="px-5 pt-5 pb-3">
              <SheetTitle>Preview</SheetTitle>
              <SheetDescription>What creators will see, as it stands right now.</SheetDescription>
            </SheetHeader>
            <div className="max-h-[78dvh] overflow-y-auto px-4 pb-6">
              <LivePreview inSheet />
            </div>
          </SheetContent>
        </Sheet>

        <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{mode === "edit" ? "Discard your changes?" : "Start over?"}</DialogTitle>
              <DialogDescription>
                {mode === "edit"
                  ? "The form goes back to the campaign as it is now. Your unsaved changes on this device are cleared."
                  : mode === "duplicate"
                    ? "The form goes back to a fresh copy of the campaign. What you changed on this device is cleared."
                    : "Everything you've filled in is cleared from the form and from this device."}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="secondary">Keep going</Button>
              </DialogClose>
              <Button
                variant="destructive"
                onClick={() => {
                  setConfirmOpen(false);
                  onRestart();
                }}
              >
                <RotateCcw aria-hidden />
                {mode === "edit" ? "Discard changes" : "Start over"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </FormProvider>
    </BuilderContext.Provider>
  );
}
