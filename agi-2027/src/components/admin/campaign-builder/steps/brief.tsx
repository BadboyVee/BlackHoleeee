"use client";

import { Controller, useWatch } from "react-hook-form";
import { Shuffle } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { CharCount, describedBy, FieldSection, FormField } from "../../form-field";
import { ListBuilder } from "../../list-builder";
import { fieldId, useBuilderForm, useFieldError } from "../use-builder";

const DO_SUGGESTIONS = ["Use the paid partnership label", "Post inside your window", "Write it in your own voice", "Show the product, not a slide"];
const DONT_SUGGESTIONS = ["Don't promise returns or results", "Don't tag competitors", "Don't use the brand's logo as your avatar"];

function rowErrors(errors: unknown): (string | undefined)[] {
  if (!Array.isArray(errors)) return [];
  return errors.map((entry) => (entry as { message?: string } | undefined)?.message);
}

export function BriefStep() {
  const { control, register, formState } = useBuilderForm();
  const [about, whatToSay, keyMessage] = useWatch({ control, name: ["brief.about", "brief.whatToSay", "brief.keyMessage"] });
  const aboutError = useFieldError("brief.about");
  const sayError = useFieldError("brief.whatToSay");
  const keyError = useFieldError("brief.keyMessage");
  const dosError = useFieldError("brief.dos");
  const dontsError = useFieldError("brief.donts");
  const anglesError = useFieldError("angles");

  return (
    <div className="grid gap-5">
      <FieldSection title="The story" description="Creators read this before they claim, so keep it short and concrete.">
        <FormField
          id={fieldId("brief.about")}
          label="About the company"
          error={aboutError}
          hint="Two or three sentences: what it does and who it's for."
          aside={<CharCount value={about ?? ""} max={2000} />}
        >
          <Textarea
            id={fieldId("brief.about")}
            rows={3}
            className="min-h-24"
            placeholder="Nebula builds AI agents that run inside a company's own tools. Version 2.0 adds a visual builder anyone on a team can use."
            aria-invalid={aboutError ? true : undefined}
            aria-describedby={describedBy(fieldId("brief.about"), { hint: true, error: aboutError })}
            {...register("brief.about")}
          />
        </FormField>
        <FormField
          id={fieldId("brief.whatToSay")}
          label="What the post should say"
          error={sayError}
          hint="What to try, show or react to. Real reactions beat feature lists."
          aside={<CharCount value={whatToSay ?? ""} max={2000} />}
        >
          <Textarea
            id={fieldId("brief.whatToSay")}
            rows={3}
            className="min-h-24"
            placeholder="Try the builder for 10 minutes, then quote the launch post with what surprised you."
            aria-invalid={sayError ? true : undefined}
            aria-describedby={describedBy(fieldId("brief.whatToSay"), { hint: true, error: sayError })}
            {...register("brief.whatToSay")}
          />
        </FormField>
        <FormField
          id={fieldId("brief.keyMessage")}
          label="Key message"
          error={keyError}
          hint="The one line every post has to land, whatever the angle."
          aside={<CharCount value={keyMessage ?? ""} max={280} />}
        >
          <Input
            id={fieldId("brief.keyMessage")}
            placeholder="Anyone on your team can build a working agent in an afternoon."
            aria-invalid={keyError ? true : undefined}
            aria-describedby={describedBy(fieldId("brief.keyMessage"), { hint: true, error: keyError })}
            {...register("brief.keyMessage")}
          />
        </FormField>
      </FieldSection>

      <FieldSection title="Do's and don'ts" description="Short rules creators can check their post against. Up to 12 each.">
        <div className="grid gap-5 md:grid-cols-2">
          <Controller
            control={control}
            name="brief.dos"
            render={({ field }) => (
              <FormField id={fieldId("brief.dos")} label="Do" error={dosError}>
                <ListBuilder
                  id={fieldId("brief.dos")}
                  defaultItems={field.value ?? []}
                  onChange={field.onChange}
                  placeholder="Add a do"
                  max={12}
                  maxLength={200}
                  suggestions={DO_SUGGESTIONS}
                  rowErrors={rowErrors(formState.errors.brief?.dos)}
                />
              </FormField>
            )}
          />
          <Controller
            control={control}
            name="brief.donts"
            render={({ field }) => (
              <FormField id={fieldId("brief.donts")} label="Don't" error={dontsError}>
                <ListBuilder
                  id={fieldId("brief.donts")}
                  defaultItems={field.value ?? []}
                  onChange={field.onChange}
                  placeholder="Add a don't"
                  max={12}
                  maxLength={200}
                  suggestions={DONT_SUGGESTIONS}
                  rowErrors={rowErrors(formState.errors.brief?.donts)}
                />
              </FormField>
            )}
          />
        </div>
      </FieldSection>

      <FieldSection
        title="Angles"
        description="Suggested hooks, so posts don't all sound the same."
        aside={<Shuffle className="mt-0.5 size-4 shrink-0 text-subtle-foreground" aria-hidden />}
      >
        <Controller
          control={control}
          name="angles"
          render={({ field }) => (
            <FormField
              id={fieldId("angles")}
              label="Angles"
              optional
              error={anglesError}
              hint="Creators see the list on the brief. After people claim, give each creator one angle from the roster, so ten posts tell ten stories. Put your favorite first."
            >
              <ListBuilder
                id={fieldId("angles")}
                defaultItems={field.value ?? []}
                onChange={field.onChange}
                placeholder="A hook, a story or a test creators can run"
                addLabel="Add angle"
                max={20}
                maxLength={280}
                ordered
                emptyText="No angles yet. Add two or three, one per line."
                rowErrors={rowErrors(formState.errors.angles)}
                aria-describedby={`${fieldId("angles")}-hint`}
              />
            </FormField>
          )}
        />
      </FieldSection>
    </div>
  );
}
