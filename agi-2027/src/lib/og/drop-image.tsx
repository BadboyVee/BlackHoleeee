import { ImageResponse } from "next/og";

import { ogFonts } from "./fonts";

/*
 * Link preview images in the Drop look: a juicy red field, one giant Anton
 * word, the thing we sell standing in front of it, and the AGI 2027 wordmark.
 * Satori draws these, so the colors are written out here (it can't read CSS
 * variables) and every box is flex. Text stays plain ASCII: a missing glyph
 * would make next/og fetch a font from the network.
 */

export const OG_SIZE = { width: 1200, height: 630 };

const RED = "#e0252b";
const RED_LIGHT = "#f2493b";
const RED_SHADE = "#9e1015";
const INK = "#16120f";
const MUTED = "#5c554f";
const PAPER = "#fffdfb";
const LINE = "#e9e2d8";

/** Fit a word across the image: Anton's capitals average about 0.53em wide. */
export function ogWordSize(word: string, maxWidth = 1100, max = 360): number {
  return Math.min(max, Math.floor(maxWidth / (word.length * 0.53)));
}

/** The AGI 2027 four-point spark. */
function Spark({ size, color }: { size: number; color: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <path
        d="M12 1.5c.55 6.15 4.35 9.95 10.5 10.5-6.15.55-9.95 4.35-10.5 10.5-.55-6.15-4.35-9.95-10.5-10.5 6.15-.55 9.95-4.35 10.5-10.5Z"
        fill={color}
      />
    </svg>
  );
}

function Arrow({ size, color }: { size: number; color: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

type DropImageOptions = {
  /** The giant word behind everything. */
  word: string;
  /** A short tag top right, like "For creators". */
  kicker: string;
  /** One line at the bottom left. */
  line: string;
  /** The white pill bottom right. */
  cta: string;
  /** What stands in front of the word. */
  children?: React.ReactNode;
};

export function dropImage({ word, kicker, line, cta, children }: DropImageOptions): ImageResponse {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          position: "relative",
          overflow: "hidden",
          backgroundColor: RED,
          backgroundImage: `radial-gradient(circle at 50% 42%, ${RED_LIGHT} 0%, ${RED} 46%, ${RED_SHADE} 100%)`,
          color: "white",
          fontFamily: "Geist, Anton",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 120,
            display: "flex",
            justifyContent: "center",
            fontFamily: "Anton",
            fontSize: ogWordSize(word),
            lineHeight: 1,
            letterSpacing: 2,
            textTransform: "uppercase",
          }}
        >
          {word}
        </div>

        {children ? (
          <div style={{ position: "absolute", left: 0, top: 0, width: 1200, height: 630, display: "flex" }}>{children}</div>
        ) : null}

        <div
          style={{
            position: "absolute",
            top: 44,
            left: 56,
            right: 56,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <Spark size={34} color="white" />
            <div style={{ display: "flex", fontFamily: "Anton", fontSize: 46, lineHeight: 1, letterSpacing: 1 }}>AGI 2027</div>
          </div>
          <div
            style={{
              display: "flex",
              padding: "10px 22px",
              borderRadius: 999,
              border: "2px solid rgba(255,255,255,0.55)",
              fontSize: 24,
            }}
          >
            {kicker}
          </div>
        </div>

        <div
          style={{
            position: "absolute",
            bottom: 44,
            left: 56,
            right: 56,
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "space-between",
            gap: 40,
          }}
        >
          <div style={{ display: "flex", maxWidth: 600, fontSize: 30, lineHeight: 1.3, color: "rgba(255,255,255,0.95)" }}>
            {line}
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "16px 26px",
              borderRadius: 999,
              backgroundColor: "white",
              color: INK,
              fontSize: 26,
              boxShadow: "0 12px 30px rgba(80,0,0,0.3)",
            }}
          >
            {cta}
            <Arrow size={24} color={INK} />
          </div>
        </div>
      </div>
    ),
    { ...OG_SIZE, fonts: ogFonts },
  );
}

/* ---------------------------------------------------------- foregrounds */

/** A launch post, standing in front of the word like the phone in the Drop hero. */
export function OgLaunchPost() {
  const bar = (width: number) => (
    <div style={{ display: "flex", width, height: 14, borderRadius: 999, backgroundColor: LINE }} />
  );
  return (
    <div
      style={{
        position: "absolute",
        left: 430,
        top: 128,
        width: 340,
        display: "flex",
        flexDirection: "column",
        gap: 16,
        padding: 26,
        borderRadius: 36,
        backgroundColor: PAPER,
        color: INK,
        boxShadow: "0 40px 80px rgba(70,0,0,0.45)",
        transform: "rotate(-5deg)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <div
          style={{
            display: "flex",
            width: 52,
            height: 52,
            borderRadius: 999,
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: RED,
          }}
        >
          <Spark size={26} color="white" />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {bar(150)}
          {bar(96)}
        </div>
      </div>
      {/* The opening words of a real launch post, Kled V3 (src/lib/showcase-posts.ts). */}
      <div style={{ display: "flex", fontSize: 24, lineHeight: 1.3 }}>This is Kled V3.</div>
      <div
        style={{
          display: "flex",
          height: 128,
          borderRadius: 22,
          alignItems: "center",
          justifyContent: "center",
          backgroundImage: "linear-gradient(135deg, #1e6bff 0%, #5b2ee8 100%)",
        }}
      >
        <Spark size={64} color="white" />
      </div>
      <div style={{ display: "flex", gap: 22, alignItems: "center" }}>
        {[54, 44, 64].map((width, index) => (
          <div key={index} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ display: "flex", width: 18, height: 18, borderRadius: 999, border: `3px solid ${MUTED}` }} />
            {bar(width)}
          </div>
        ))}
      </div>
    </div>
  );
}

/** The Book a campaign form, in short. */
export function OgBookingForm() {
  const field = (label: string, value: string) => (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ display: "flex", fontSize: 16, color: MUTED }}>{label}</div>
      <div
        style={{
          display: "flex",
          padding: "11px 16px",
          borderRadius: 14,
          border: `2px solid ${LINE}`,
          fontSize: 20,
        }}
      >
        {value}
      </div>
    </div>
  );
  return (
    <div
      style={{
        position: "absolute",
        left: 420,
        top: 124,
        width: 360,
        display: "flex",
        flexDirection: "column",
        gap: 14,
        padding: 28,
        borderRadius: 36,
        backgroundColor: PAPER,
        color: INK,
        boxShadow: "0 40px 80px rgba(70,0,0,0.45)",
        transform: "rotate(4deg)",
      }}
    >
      <div style={{ display: "flex", fontFamily: "Anton", fontSize: 40, lineHeight: 1, textTransform: "uppercase" }}>
        Book a campaign
      </div>
      {field("What you're launching", "Our open beta")}
      {field("Budget", "$10k to $25k")}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 10,
          marginTop: 4,
          padding: "14px 0",
          borderRadius: 999,
          backgroundColor: INK,
          color: "white",
          fontSize: 20,
        }}
      >
        Send it
        <Arrow size={20} color="white" />
      </div>
    </div>
  );
}
