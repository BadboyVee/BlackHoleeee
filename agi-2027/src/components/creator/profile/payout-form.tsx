"use client";

import { startTransition, useActionState, useId, useRef, useState } from "react";
import { useForm, useWatch, type Resolver } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Coins, Landmark, MessageSquareText, ShieldCheck } from "lucide-react";

import { savePayoutDetails } from "@/app/dashboard/profile/actions";
import { SCROLL_MARGIN, ServerAlert, useServerErrors } from "@/components/auth/parts";
import { CharactersLeft, chipClass, CountrySelect, GroupError, IDLE, SavedNote } from "@/components/onboarding/form-kit";
import { Button } from "@/components/ui/button";
import { Field, fieldDescribedBy } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import {
  addressExample,
  assetOnNetwork,
  CRYPTO_ASSETS,
  CRYPTO_NETWORKS,
  NETWORK_VALUES,
  PAYOUT_METHODS,
  type CryptoAsset,
  type CryptoNetwork,
  type PayoutMethod,
} from "@/lib/creators/options";
import type { PayoutDetails } from "@/lib/creators/queries";
import { payoutSchema, type CreatorFormState } from "@/lib/creators/schemas";
import { cn } from "@/lib/utils";

/** Every method's fields at once. Only the chosen method's fields are on screen, and only those post. */
type PayoutFormValues = {
  method: PayoutMethod;
  asset: CryptoAsset | "";
  network: CryptoNetwork | "";
  wallet: string;
  bankCountry: string;
  bankName: string;
  accountName: string;
  accountNumber: string;
  bankCode: string;
  otherDetails: string;
};

/** The schema reads only the chosen method's fields (zod drops the rest), so the flat form fits it. */
const resolver = zodResolver(payoutSchema) as unknown as Resolver<PayoutFormValues>;

/** The fields in the order the form shows them, so focus goes to the first problem. */
const FIELDS = [
  "method",
  "asset",
  "network",
  "wallet",
  "bankCountry",
  "bankName",
  "accountName",
  "accountNumber",
  "bankCode",
  "otherDetails",
] as const;

const OTHER_LIMIT = 500;

const METHOD_ICONS = { crypto: Coins, bank: Landmark, other: MessageSquareText } as const;

function isAsset(value: string | null | undefined): value is CryptoAsset {
  return (CRYPTO_ASSETS as readonly string[]).includes(value ?? "");
}

function isNetwork(value: string | null | undefined): value is CryptoNetwork {
  return (NETWORK_VALUES as readonly string[]).includes(value ?? "");
}

function defaultsFrom(payout: PayoutDetails | null): PayoutFormValues {
  return {
    method: payout?.method ?? "crypto",
    asset: isAsset(payout?.cryptoAsset) ? payout.cryptoAsset : "",
    network: isNetwork(payout?.cryptoNetwork) ? payout.cryptoNetwork : "",
    wallet: payout?.walletAddress ?? "",
    bankCountry: payout?.bankCountry ?? "",
    bankName: payout?.bankName ?? "",
    accountName: payout?.accountName ?? "",
    accountNumber: payout?.accountNumber ?? "",
    bankCode: payout?.bankCode ?? "",
    otherDetails: payout?.otherDetails ?? "",
  };
}

/** A method as a big radio card: icon, name and a line on what it means. */
const methodCardClass = cn(
  "flex h-full min-h-11 items-start gap-3 rounded-xl border border-border-strong bg-surface p-3.5 pr-12 text-left",
  "transition-[background-color,border-color,box-shadow] duration-150 ease-snap",
  "hover:bg-surface-2/70",
  "peer-checked:border-foreground peer-checked:bg-surface-2/60 peer-checked:inset-ring peer-checked:inset-ring-foreground",
  "peer-focus-visible:ring-4 peer-focus-visible:ring-ring/25",
  "peer-disabled:cursor-not-allowed peer-disabled:opacity-60 peer-disabled:hover:bg-surface",
);

/**
 * Where to pay the creator: crypto (coin, network and wallet), a bank
 * account, or something else. Saving logs the change and emails them, so a
 * swap never goes unnoticed.
 */
export function PayoutForm({
  payout,
  locked = false,
  previewOnly = false,
}: {
  payout: PayoutDetails | null;
  /** Staff looking at the creator app: nothing can be changed. */
  locked?: boolean;
  /** Supabase isn't connected: the form can be tried, and says nothing is saved. */
  previewOnly?: boolean;
}) {
  const uid = useId();
  const id = (name: string) => `${uid}-${name}`;
  const [state, dispatch, pending] = useActionState(savePayoutDetails, IDLE);
  const [dismissed, setDismissed] = useState<CreatorFormState | null>(null);
  // Fixed at first render. Each field also gets its default as a prop, so the
  // server's HTML shows the saved details before the page's JavaScript runs.
  const [defaults] = useState(() => defaultsFrom(payout));
  const form = useForm<PayoutFormValues>({
    resolver,
    mode: "onTouched",
    reValidateMode: "onChange",
    defaultValues: defaults,
  });
  const errors = form.formState.errors;
  const alertRef = useRef<HTMLDivElement>(null);
  useServerErrors(state, form, FIELDS, alertRef);

  const method = useWatch({ control: form.control, name: "method" });
  const asset = useWatch({ control: form.control, name: "asset" });
  const network = useWatch({ control: form.control, name: "network" });
  const otherDetails = useWatch({ control: form.control, name: "otherDetails" }) ?? "";
  const shown = dismissed === state ? IDLE : state;
  const failure = shown.status === "error" ? shown : null;

  const networks = CRYPTO_NETWORKS.filter((option) => !asset || (option.assets as readonly string[]).includes(asset));
  const networkHint = asset ? `The networks we send ${asset} on. Check your wallet supports the one you pick.` : "Pick the coin first.";
  const walletHint = network ? `It should be ${addressExample(network)}.` : "Pick the network first.";

  const methodField = form.register("method", {
    // Another method's old problems shouldn't follow the creator back to it.
    onChange: () => form.clearErrors(),
  });
  const assetField = form.register("asset", {
    // A coin the chosen network doesn't carry: the network starts over.
    onChange: (event: React.ChangeEvent<HTMLInputElement>) => {
      const current = form.getValues("network");
      if (current && !assetOnNetwork(event.target.value, current)) form.setValue("network", "");
    },
  });
  const networkField = form.register("network", {
    // The address format depends on the network, so check the address again.
    onChange: () => {
      if (form.getFieldState("wallet").isTouched) void form.trigger("wallet");
    },
  });

  const describe = (name: string, hint?: string, error?: unknown) => ({
    id: id(name),
    "aria-invalid": error ? true : undefined,
    "aria-describedby": fieldDescribedBy(id(name), { hint, error }),
    className: SCROLL_MARGIN,
  });

  return (
    <form
      action={dispatch}
      onSubmit={(event) => {
        const element = event.currentTarget;
        setDismissed(state);
        void form.handleSubmit(() => startTransition(() => dispatch(new FormData(element))))(event);
      }}
      onChange={() => {
        if (state.status === "saved" && dismissed !== state) setDismissed(state);
      }}
      noValidate
      aria-label="Payout details"
    >
      <fieldset disabled={locked} className="grid min-w-0 gap-7">
        <fieldset className="min-w-0">
          <legend className="mb-3 text-sm leading-none font-medium">How should we pay you?</legend>
          <div className="grid gap-2 sm:grid-cols-3">
            {PAYOUT_METHODS.map((option) => {
              const Icon = METHOD_ICONS[option.value];
              return (
                <label key={option.value} className="relative block cursor-pointer has-disabled:cursor-not-allowed">
                  <input
                    type="radio"
                    value={option.value}
                    defaultChecked={defaults.method === option.value}
                    className={cn("peer sr-only", SCROLL_MARGIN)}
                    {...methodField}
                  />
                  <span className={methodCardClass}>
                    <span
                      aria-hidden
                      className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-surface-2 text-muted-foreground"
                    >
                      <Icon className="size-[18px]" />
                    </span>
                    <span className="min-w-0">
                      <span className="block text-[15px] leading-tight font-medium">{option.label}</span>
                      <span className="mt-1 block text-[13px] leading-snug text-pretty text-muted-foreground">{option.hint}</span>
                    </span>
                  </span>
                  <span
                    aria-hidden
                    className="pointer-events-none absolute top-3.5 right-3.5 size-5 rounded-full border-2 border-border-strong bg-surface transition-[border-width,border-color] duration-150 ease-snap peer-checked:border-[6px] peer-checked:border-foreground"
                  />
                </label>
              );
            })}
          </div>
        </fieldset>

        {method === "crypto" ? (
          <div className="grid gap-5">
            <fieldset
              aria-describedby={errors.asset ? `${id("asset")}-error` : undefined}
              aria-invalid={errors.asset ? true : undefined}
              className="group/asset min-w-0"
            >
              <legend className="mb-3 text-sm leading-none font-medium">Coin</legend>
              <div className="flex flex-wrap gap-2">
                {CRYPTO_ASSETS.map((coin) => (
                  <label key={coin} className="relative cursor-pointer has-disabled:cursor-not-allowed">
                    <input
                      type="radio"
                      value={coin}
                      defaultChecked={defaults.asset === coin}
                      className={cn("peer sr-only", SCROLL_MARGIN)}
                      {...assetField}
                    />
                    <span className={cn(chipClass, "min-w-24 justify-center", "group-aria-invalid/asset:border-destructive-text")}>
                      {coin}
                    </span>
                  </label>
                ))}
              </div>
              <GroupError id={`${id("asset")}-error`} message={errors.asset?.message} />
            </fieldset>

            <Field id={id("network")} label="Network" hint={networkHint} error={errors.network?.message}>
              <NativeSelect {...describe("network", networkHint, errors.network)} defaultValue={defaults.network} {...networkField}>
                <option value="">Pick a network</option>
                {networks.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </NativeSelect>
            </Field>

            <Field id={id("wallet")} label="Wallet address" hint={walletHint} error={errors.wallet?.message}>
              <Input
                {...describe("wallet", walletHint, errors.wallet)}
                type="text"
                autoComplete="off"
                autoCapitalize="none"
                autoCorrect="off"
                spellCheck={false}
                maxLength={120}
                placeholder="Paste it from your wallet app"
                className={cn(SCROLL_MARGIN, "font-mono")}
                defaultValue={defaults.wallet}
                {...form.register("wallet")}
              />
            </Field>
          </div>
        ) : null}

        {method === "bank" ? (
          <div className="grid gap-5 sm:grid-cols-2 sm:gap-4">
            <Field id={id("bankCountry")} label="Country of the bank" error={errors.bankCountry?.message}>
              <CountrySelect
                id={id("bankCountry")}
                error={errors.bankCountry?.message}
                defaultValue={defaults.bankCountry}
                register={form.register("bankCountry")}
              />
            </Field>
            <Field id={id("bankName")} label="Bank name" error={errors.bankName?.message}>
              <Input
                {...describe("bankName", undefined, errors.bankName)}
                type="text"
                autoComplete="off"
                maxLength={120}
                required
                defaultValue={defaults.bankName}
                {...form.register("bankName")}
              />
            </Field>
            <Field id={id("accountName")} label="Name on the account" error={errors.accountName?.message}>
              <Input
                {...describe("accountName", undefined, errors.accountName)}
                type="text"
                autoComplete="off"
                maxLength={120}
                required
                defaultValue={defaults.accountName}
                {...form.register("accountName")}
              />
            </Field>
            <Field id={id("accountNumber")} label="Account number or IBAN" error={errors.accountNumber?.message}>
              <Input
                {...describe("accountNumber", undefined, errors.accountNumber)}
                type="text"
                autoComplete="off"
                autoCapitalize="characters"
                autoCorrect="off"
                spellCheck={false}
                maxLength={40}
                required
                className={cn(SCROLL_MARGIN, "font-mono")}
                defaultValue={defaults.accountNumber}
                {...form.register("accountNumber")}
              />
            </Field>
            <Field id={id("bankCode")} label="Sort code, routing number or SWIFT" optional error={errors.bankCode?.message}>
              <Input
                {...describe("bankCode", undefined, errors.bankCode)}
                type="text"
                autoComplete="off"
                autoCapitalize="characters"
                autoCorrect="off"
                spellCheck={false}
                maxLength={40}
                className={cn(SCROLL_MARGIN, "font-mono")}
                defaultValue={defaults.bankCode}
                {...form.register("bankCode")}
              />
            </Field>
          </div>
        ) : null}

        {method === "other" ? (
          <Field
            id={id("otherDetails")}
            label="How should we pay you?"
            hint="Who to pay, where, and in which currency."
            error={errors.otherDetails?.message}
          >
            <Textarea
              {...describe("otherDetails", "Who to pay, where, and in which currency.", errors.otherDetails)}
              rows={4}
              maxLength={OTHER_LIMIT}
              required
              defaultValue={defaults.otherDetails}
              {...form.register("otherDetails")}
            />
            <CharactersLeft value={otherDetails} limit={OTHER_LIMIT} />
          </Field>
        ) : null}

        <div className="grid gap-4 border-t pt-6">
          {failure && !failure.fieldErrors ? <ServerAlert ref={alertRef} message={failure.message} /> : null}
          <p className="flex items-start gap-2.5 text-[13px] leading-relaxed text-pretty text-muted-foreground">
            <ShieldCheck className="mt-0.5 size-4 shrink-0" aria-hidden />
            Only you and the agency admin can see these. We email you whenever they change.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
            <Button type="submit" size="lg" loading={pending} className="w-full sm:w-auto">
              {pending ? "Saving" : "Save payout details"}
            </Button>
            <SavedNote state={shown} />
          </div>
          {previewOnly ? (
            <p className="text-[13px] text-pretty text-muted-foreground">
              This is a preview. Accounts aren&apos;t connected yet, so nothing is saved.
            </p>
          ) : null}
        </div>
      </fieldset>
    </form>
  );
}
