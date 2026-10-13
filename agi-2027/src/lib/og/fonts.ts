import "server-only";

import { readFile } from "node:fs/promises";
import { join } from "node:path";

/*
 * Fonts for the link preview images, read from local files only, never
 * fetched at runtime. Anton comes from the pinned @fontsource/anton package
 * (Satori reads woff, not woff2). Geist Regular is the file next/og itself
 * ships as its default font; if a Next upgrade moves it, the images still
 * render, with Anton for every line.
 */

const ANTON_FILE = join(process.cwd(), "node_modules/@fontsource/anton/files/anton-latin-400-normal.woff");
const GEIST_FILE = join(process.cwd(), "node_modules/next/dist/compiled/@vercel/og/Geist-Regular.ttf");

export type OgFont = { name: string; data: ArrayBuffer; weight: 400; style: "normal" };

async function read(name: string, file: string): Promise<OgFont | null> {
  try {
    const data = await readFile(file);
    return { name, data: Uint8Array.from(data).buffer, weight: 400, style: "normal" };
  } catch {
    return null;
  }
}

async function loadOgFonts(): Promise<OgFont[]> {
  const fonts = (await Promise.all([read("Anton", ANTON_FILE), read("Geist", GEIST_FILE)])).filter(
    (font): font is OgFont => font !== null,
  );
  if (!fonts.some((font) => font.name === "Anton")) {
    throw new Error(`Anton font missing at ${ANTON_FILE}. Run npm install.`);
  }
  return fonts;
}

/**
 * Anton first (the display face), then Geist for small text. Read once, at
 * module scope: the files never change between requests, so Cache Components
 * treats them as part of the prerender instead of request-time data.
 */
export const ogFonts: OgFont[] = await loadOgFonts();
