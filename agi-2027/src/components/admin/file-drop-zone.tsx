"use client";

import { useId, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { CircleAlert, FileText, Film, ImageIcon, UploadCloud, X } from "lucide-react";

import type { AssetKind } from "@/lib/campaigns/options";
import { cn } from "@/lib/utils";
import { springArrive } from "./motion";

export type ChosenFile = { name: string; kind: AssetKind; sizeBytes: number };

const MAX_BYTES = 200 * 1024 * 1024;

export function assetKindOf(file: { type: string; name: string }): AssetKind {
  if (file.type.startsWith("image/") || /\.(png|jpe?g|gif|webp|avif|svg)$/i.test(file.name)) return "image";
  if (file.type.startsWith("video/") || /\.(mp4|mov|webm|m4v)$/i.test(file.name)) return "video";
  return "document";
}

/** "1.8 MB", "640 KB". */
export function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value >= 10 ? Math.round(value) : value.toFixed(1)} ${units[unit]}`;
}

const kindIcon = { image: ImageIcon, video: Film, document: FileText } as const;
const kindLabel = { image: "Image", video: "Video", document: "Document" } as const;

/**
 * Drop files or pick them. Files are only listed (name, kind, size) for now;
 * uploading to storage arrives in Milestone 5.
 */
export function FileDropZone({
  files,
  onChange,
  max = 20,
}: {
  files: ChosenFile[];
  onChange: (files: ChosenFile[]) => void;
  max?: number;
}) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const next = [...files];
    const skipped: string[] = [];
    for (const file of Array.from(list)) {
      if (next.length >= max) {
        skipped.push(`${file.name} (the limit is ${max} files)`);
        continue;
      }
      if (file.size > MAX_BYTES) {
        skipped.push(`${file.name} (over 200 MB)`);
        continue;
      }
      if (next.some((entry) => entry.name === file.name && entry.sizeBytes === file.size)) continue;
      next.push({ name: file.name, kind: assetKindOf(file), sizeBytes: file.size });
    }
    onChange(next);
    setProblem(skipped.length ? `Skipped ${skipped.join(", ")}.` : null);
  }

  return (
    <div className="grid gap-2.5">
      <label
        htmlFor={inputId}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          addFiles(event.dataTransfer.files);
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-7 text-center transition-colors",
          "focus-within:border-ring focus-within:ring-4 focus-within:ring-ring/20",
          dragging ? "border-foreground bg-surface-2" : "border-border-strong bg-surface-2/30 hover:bg-surface-2/60",
        )}
      >
        <span className="flex size-10 items-center justify-center rounded-full border bg-surface">
          <UploadCloud className="size-5 text-muted-foreground" aria-hidden />
        </span>
        <span className="text-sm font-medium">
          {dragging ? "Drop to add" : "Drop images, videos or documents"}
          {dragging ? null : <span className="text-muted-foreground">, or choose files</span>}
        </span>
        <span className="text-xs text-muted-foreground">Up to {max} files, 200 MB each. Listed now, uploaded from Milestone 5.</span>
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          multiple
          className="sr-only"
          onChange={(event) => {
            addFiles(event.target.files);
            event.target.value = "";
          }}
        />
      </label>

      {problem ? (
        <p role="alert" className="flex items-start gap-1.5 text-[13px] leading-snug text-destructive-text">
          <CircleAlert className="mt-px size-3.5 shrink-0" aria-hidden />
          {problem}
        </p>
      ) : null}

      {files.length ? (
        <ul className="grid gap-1.5" aria-label="Chosen files">
          <AnimatePresence initial={false}>
            {files.map((file, index) => {
              const Icon = kindIcon[file.kind];
              return (
                <motion.li
                  key={`${file.name}-${file.sizeBytes}`}
                  layout
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, transition: { duration: 0.1 } }}
                  transition={springArrive}
                  className="flex min-h-12 items-center gap-3 rounded-lg border bg-surface py-1.5 pr-1.5 pl-3"
                >
                  <Icon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {kindLabel[file.kind]} · {formatBytes(file.sizeBytes)}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onChange(files.filter((_, i) => i !== index))}
                    aria-label={`Remove ${file.name}`}
                    className="flex size-9 cursor-pointer items-center justify-center rounded-md text-subtle-foreground transition-colors hover:bg-surface-2 hover:text-foreground pointer-coarse:size-11"
                  >
                    <X className="size-4" />
                  </button>
                </motion.li>
              );
            })}
          </AnimatePresence>
        </ul>
      ) : null}
    </div>
  );
}
