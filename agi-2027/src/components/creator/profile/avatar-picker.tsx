"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { Camera, CircleAlert, Loader2 } from "lucide-react";

import { saveAvatar } from "@/app/dashboard/profile/actions";
import { IDLE, SavedNote } from "@/components/onboarding/form-kit";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { initialsFor } from "@/lib/auth/account-display";
import {
  AVATAR_BUCKET,
  AVATAR_SIZE,
  AVATAR_TYPES,
  avatarPath,
  avatarPublicUrl,
  avatarTypeProblem,
} from "@/lib/creators/avatar";
import type { CreatorFormState } from "@/lib/creators/schemas";
import { createClient } from "@/lib/supabase/client";

const ACCEPT = AVATAR_TYPES.join(",");
const UPLOAD_FAILED = "That photo didn't upload. Try again.";

/**
 * Crops the middle square of the picture and draws it at AVATAR_SIZE pixels.
 * WebP where the browser can write it; Safari can't, so it gets JPEG instead,
 * on a white background since JPEG has no transparency.
 */
async function squarePhoto(file: File): Promise<Blob> {
  const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  try {
    const side = Math.min(bitmap.width, bitmap.height);
    const canvas = document.createElement("canvas");
    canvas.width = AVATAR_SIZE;
    canvas.height = AVATAR_SIZE;
    const context = canvas.getContext("2d");
    if (!context || side === 0) throw new Error("Can't draw this image");
    context.imageSmoothingEnabled = true;
    context.imageSmoothingQuality = "high";
    const draw = () =>
      context.drawImage(bitmap, (bitmap.width - side) / 2, (bitmap.height - side) / 2, side, side, 0, 0, AVATAR_SIZE, AVATAR_SIZE);
    const encode = (type: string) => new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, type, 0.86));

    draw();
    const webp = await encode("image/webp");
    if (webp?.type === "image/webp") return webp;

    // Image pixels, not page styling: JPEG needs a solid backdrop.
    context.fillStyle = "white";
    context.fillRect(0, 0, AVATAR_SIZE, AVATAR_SIZE);
    draw();
    const jpeg = await encode("image/jpeg");
    if (jpeg) return jpeg;
    throw new Error("Can't encode this image");
  } finally {
    bitmap.close();
  }
}

/**
 * The profile photo: shows it (or the initials), and changes it. The browser
 * crops and shrinks the picture, uploads it straight to the avatars bucket,
 * then the server saves its address on the profile.
 */
export function AvatarPicker({
  userId,
  name,
  handle,
  avatarUrl,
  supabaseUrl,
  locked = false,
  lockedNote,
}: {
  userId: string;
  name: string;
  handle: string | null;
  avatarUrl: string | null;
  /** The Supabase project's address, or null on a preview without accounts. */
  supabaseUrl: string | null;
  /** True when the photo can't be changed here: a preview, or staff looking. */
  locked?: boolean;
  /** Says why, under the buttons. */
  lockedNote?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [pending, startTransition] = useTransition();
  const [task, setTask] = useState<"upload" | "remove" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CreatorFormState>(IDLE);
  /*
   * What the circle shows until the page catches up: the new picture itself
   * (a local copy, so it never blinks back to the initials while the saved
   * one loads), or nothing once the photo is removed. Null: the saved photo.
   */
  const [override, setOverride] = useState<{ url: string | null } | null>(null);
  const localUrl = override?.url?.startsWith("blob:") ? override.url : null;
  useEffect(() => {
    if (!localUrl) return;
    return () => URL.revokeObjectURL(localUrl);
  }, [localUrl]);

  const disabled = locked || !supabaseUrl;
  const shown = override ? override.url : avatarUrl;
  const uploading = pending && task === "upload";
  const removing = pending && task === "remove";

  function upload(file: File) {
    if (!supabaseUrl) return;
    const problem = avatarTypeProblem(file.type, file.size);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setResult(IDLE);
    setTask("upload");
    startTransition(async () => {
      let photo: Blob;
      try {
        photo = await squarePhoto(file);
      } catch {
        setError("We couldn't read that image. Try another one.");
        return;
      }
      setOverride({ url: URL.createObjectURL(photo) });

      try {
        const { error: uploadError } = await createClient()
          .storage.from(AVATAR_BUCKET)
          .upload(avatarPath(userId), photo, { upsert: true, contentType: photo.type || "image/webp", cacheControl: "3600" });
        if (uploadError) throw uploadError;
      } catch {
        setOverride(null);
        setError(UPLOAD_FAILED);
        return;
      }

      const saved = await saveAvatar(avatarPublicUrl(supabaseUrl, userId, Date.now())).catch(
        (): CreatorFormState => ({ status: "error", message: UPLOAD_FAILED }),
      );
      if (saved.status === "error") {
        setOverride(null);
        setError(saved.message);
        return;
      }
      setResult(saved);
    });
  }

  function remove() {
    setError(null);
    setResult(IDLE);
    setTask("remove");
    startTransition(async () => {
      const saved = await saveAvatar(null).catch(
        (): CreatorFormState => ({ status: "error", message: "We couldn't remove it just now. Try again in a minute." }),
      );
      if (saved.status === "error") {
        setError(saved.message);
        return;
      }
      setOverride({ url: null });
      setResult(saved);
    });
  }

  return (
    <div className="flex flex-col items-center gap-5 text-center sm:flex-row sm:items-center sm:gap-6 sm:text-left">
      <div className="relative shrink-0">
        <Avatar className="size-24 shadow-soft ring-4 ring-surface-2 sm:size-28">
          {shown ? <AvatarImage src={shown} alt="Your photo" /> : null}
          <AvatarFallback className="bg-foreground font-mono text-[1.75rem] font-semibold tracking-tight text-background sm:text-[2rem]">
            {initialsFor(name || "?")}
          </AvatarFallback>
        </Avatar>
        {pending ? (
          <span
            aria-hidden
            className="absolute inset-0 flex items-center justify-center rounded-full bg-background/55 text-foreground backdrop-blur-[2px]"
          >
            <Loader2 className="size-6 animate-spin" />
          </span>
        ) : null}
      </div>

      <div className="grid min-w-0 justify-items-center gap-3 sm:justify-items-start">
        <div className="min-w-0 max-w-full">
          <p className="truncate text-[17px] font-semibold tracking-[-0.02em]">{name || "Your name"}</p>
          {handle ? <p className="truncate text-sm text-muted-foreground">@{handle}</p> : null}
        </div>

        <div className="flex flex-wrap justify-center gap-2 sm:justify-start">
          <Button
            type="button"
            variant="secondary"
            size="lg"
            loading={uploading}
            disabled={disabled || pending}
            onClick={() => inputRef.current?.click()}
          >
            {uploading ? null : <Camera aria-hidden />}
            {uploading ? "Uploading" : shown ? "Change photo" : "Add a photo"}
          </Button>
          {shown ? (
            <Button type="button" variant="ghost" size="lg" loading={removing} disabled={disabled || pending} onClick={remove}>
              {removing ? "Removing" : "Remove photo"}
            </Button>
          ) : null}
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            hidden
            tabIndex={-1}
            disabled={disabled}
            onChange={(event) => {
              const file = event.target.files?.[0];
              // Cleared so picking the same file again still counts as a change.
              event.target.value = "";
              if (file) upload(file);
            }}
          />
        </div>

        <p className="text-[13px] leading-snug text-pretty text-muted-foreground">
          {disabled && lockedNote ? lockedNote : "JPG, PNG or WebP. We crop it to a square."}
        </p>
        {error ? (
          <p role="alert" className="flex items-start gap-1.5 text-left text-[13px] leading-snug text-destructive-text">
            <CircleAlert className="mt-px size-3.5 shrink-0" aria-hidden />
            {error}
          </p>
        ) : null}
        <SavedNote state={result} />
        <span className="sr-only" aria-live="polite">
          {uploading ? "Uploading your photo" : removing ? "Removing your photo" : ""}
        </span>
      </div>
    </div>
  );
}
