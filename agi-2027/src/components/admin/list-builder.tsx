"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowDown, ArrowUp, Check, CircleAlert, Pencil, Plus, Trash2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { fieldControlClass } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { springArrive, springMove } from "./motion";

type Row = { key: string; value: string };

let rowSeq = 0;
const nextKey = () => `row-${++rowSeq}`;

type ListBuilderProps = {
  id: string;
  /** The starting items. The builder owns its rows after mount and reports every change. */
  defaultItems: string[];
  onChange: (next: string[]) => void;
  placeholder: string;
  addLabel?: string;
  max: number;
  maxLength: number;
  /** Show numbers and move buttons (angles). */
  ordered?: boolean;
  /** One-tap starters, hidden once added. */
  suggestions?: string[];
  emptyText?: string;
  /** Errors from the form for individual rows, by index. */
  rowErrors?: (string | undefined)[];
  "aria-describedby"?: string;
};

/**
 * A short list people build one line at a time: add, edit in place, remove,
 * and (for ordered lists) move up or down. Enter adds or saves, Escape
 * cancels an edit.
 */
export function ListBuilder({
  id,
  defaultItems,
  onChange,
  placeholder,
  addLabel = "Add",
  max,
  maxLength,
  ordered = false,
  suggestions = [],
  emptyText,
  rowErrors = [],
  ...aria
}: ListBuilderProps) {
  const [rows, setRows] = useState<Row[]>(() => defaultItems.map((value) => ({ key: nextKey(), value })));
  const [draft, setDraft] = useState("");
  const [editing, setEditing] = useState<{ key: string; value: string } | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  function commit(next: Row[]) {
    setRows(next);
    onChange(next.map((row) => row.value));
  }

  function check(value: string, exceptKey?: string): string | null {
    const text = value.trim();
    if (!text) return "Write something first.";
    if (text.length > maxLength) return `Keep it under ${maxLength} characters.`;
    if (rows.some((row) => row.key !== exceptKey && row.value.toLowerCase() === text.toLowerCase())) {
      return "That's already on the list.";
    }
    return null;
  }

  function add(value = draft) {
    if (rows.length >= max) {
      setProblem(`Up to ${max}. Remove one to add another.`);
      return;
    }
    const issue = check(value);
    if (issue) {
      setProblem(issue);
      return;
    }
    commit([...rows, { key: nextKey(), value: value.trim() }]);
    if (value === draft) setDraft("");
    setProblem(null);
  }

  function saveEdit() {
    if (!editing) return;
    const issue = check(editing.value, editing.key);
    if (issue) {
      setProblem(issue);
      return;
    }
    commit(rows.map((row) => (row.key === editing.key ? { ...row, value: editing.value.trim() } : row)));
    setEditing(null);
    setProblem(null);
  }

  function move(index: number, delta: -1 | 1) {
    const target = index + delta;
    if (target < 0 || target >= rows.length) return;
    const next = [...rows];
    [next[index], next[target]] = [next[target], next[index]];
    commit(next);
  }

  const remaining = suggestions.filter((suggestion) => !rows.some((row) => row.value.toLowerCase() === suggestion.toLowerCase()));
  const full = rows.length >= max;

  return (
    <div className="grid gap-2.5">
      {rows.length ? (
        <ol className="grid gap-1.5" aria-label="Items">
          <AnimatePresence initial={false}>
            {rows.map((row, index) => {
              const isEditing = editing?.key === row.key;
              const rowError = rowErrors[index];
              return (
                <motion.li
                  key={row.key}
                  layout
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, transition: { duration: 0.1 } }}
                  transition={{ default: springArrive, layout: springMove }}
                  className={cn(
                    "group flex min-h-11 items-start gap-2 rounded-lg border bg-surface py-1.5 pr-1.5 pl-3",
                    rowError ? "border-destructive-text" : "border-border",
                  )}
                >
                  <span
                    aria-hidden
                    className={cn(
                      "mt-[7px] shrink-0 font-mono text-[11px] text-subtle-foreground tabular",
                      ordered ? "w-4" : "w-1.5",
                    )}
                  >
                    {ordered ? index + 1 : <span className="mt-[5px] block size-1.5 rounded-full bg-border-strong" />}
                  </span>
                  {isEditing ? (
                    <input
                      // Editing starts from a click on Edit, so moving focus here is expected.
                      autoFocus
                      value={editing.value}
                      onChange={(event) => setEditing({ key: row.key, value: event.target.value })}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          saveEdit();
                        } else if (event.key === "Escape") {
                          event.preventDefault();
                          setEditing(null);
                          setProblem(null);
                        }
                      }}
                      aria-label={`Edit item ${index + 1}`}
                      className="h-8 min-w-0 flex-1 rounded-md border border-input bg-surface px-2 text-base outline-none focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/20 sm:text-sm"
                    />
                  ) : (
                    <p className="min-w-0 flex-1 py-1 text-sm leading-relaxed text-pretty break-words">{row.value}</p>
                  )}
                  <div className="flex shrink-0 items-center">
                    {isEditing ? (
                      <>
                        <IconButton label="Save" onClick={saveEdit}>
                          <Check />
                        </IconButton>
                        <IconButton
                          label="Cancel"
                          onClick={() => {
                            setEditing(null);
                            setProblem(null);
                          }}
                        >
                          <X />
                        </IconButton>
                      </>
                    ) : (
                      <>
                        {ordered ? (
                          <>
                            <IconButton label={`Move item ${index + 1} up`} disabled={index === 0} onClick={() => move(index, -1)}>
                              <ArrowUp />
                            </IconButton>
                            <IconButton
                              label={`Move item ${index + 1} down`}
                              disabled={index === rows.length - 1}
                              onClick={() => move(index, 1)}
                            >
                              <ArrowDown />
                            </IconButton>
                          </>
                        ) : null}
                        <IconButton label={`Edit item ${index + 1}`} onClick={() => setEditing({ key: row.key, value: row.value })}>
                          <Pencil />
                        </IconButton>
                        <IconButton label={`Remove item ${index + 1}`} onClick={() => commit(rows.filter((entry) => entry.key !== row.key))}>
                          <Trash2 />
                        </IconButton>
                      </>
                    )}
                  </div>
                </motion.li>
              );
            })}
          </AnimatePresence>
        </ol>
      ) : emptyText ? (
        <p className="rounded-lg border border-dashed px-3 py-3 text-[13px] text-muted-foreground">{emptyText}</p>
      ) : null}

      <div className="flex gap-2">
        <input
          id={id}
          value={draft}
          disabled={full}
          onChange={(event) => {
            setDraft(event.target.value);
            if (problem) setProblem(null);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              add();
            }
          }}
          placeholder={full ? `That's the limit of ${max}` : placeholder}
          aria-describedby={[aria["aria-describedby"], problem ? `${id}-problem` : null].filter(Boolean).join(" ") || undefined}
          aria-invalid={problem ? true : undefined}
          maxLength={maxLength + 20}
          enterKeyHint="done"
          className={cn(fieldControlClass, "h-11 flex-1 px-3.5")}
        />
        <Button type="button" variant="secondary" className="h-11 shrink-0" onClick={() => add()} disabled={full}>
          <Plus aria-hidden />
          {addLabel}
        </Button>
      </div>

      {problem ? (
        <p id={`${id}-problem`} role="alert" className="flex items-start gap-1.5 text-[13px] leading-snug text-destructive-text">
          <CircleAlert className="mt-px size-3.5 shrink-0" aria-hidden />
          {problem}
        </p>
      ) : null}

      {remaining.length && !full ? (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="mr-0.5 text-xs text-subtle-foreground">Suggestions</span>
          {remaining.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => add(suggestion)}
              className="inline-flex min-h-8 cursor-pointer items-center gap-1 rounded-full border border-dashed border-border-strong px-2.5 text-xs text-muted-foreground transition-colors hover:border-solid hover:bg-surface-2 hover:text-foreground pointer-coarse:min-h-10"
            >
              <Plus className="size-3" aria-hidden />
              {suggestion}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function IconButton({
  label,
  onClick,
  disabled,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className="flex size-8 cursor-pointer items-center justify-center rounded-md text-subtle-foreground transition-colors hover:bg-surface-2 hover:text-foreground disabled:cursor-default disabled:opacity-30 disabled:hover:bg-transparent pointer-coarse:size-10 [&_svg]:size-3.5"
    >
      {children}
    </button>
  );
}
