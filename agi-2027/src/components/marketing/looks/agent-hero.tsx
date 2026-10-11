import { siteConfig } from "@/lib/site";
import { AgentStage } from "./agent-stage";
import { EchoTalks, GreetingPills, type Pill } from "./agent-greeting";

/** Each line streams in word by word, the way an assistant writes. */
const LINES = [
  { text: "Hey there, I'm Echo.", tone: "muted" as const },
  {
    text: "I get AI launches talked about by the creators people already follow.",
    tone: "headline" as const,
  },
  { text: "Glad you stopped by. What are we launching?", tone: "plain" as const },
];

const WORD_GAP_MS = 55;
const LINE_GAP_MS = 260;
const START_MS = 450;

function timeline() {
  let at = START_MS;
  return LINES.map((line) => {
    const words = line.text.split(" ").map((word) => {
      const delay = at;
      at += WORD_GAP_MS;
      return { word, delay };
    });
    at += LINE_GAP_MS;
    return { ...line, words, end: at };
  });
}

function Words({ words }: { words: { word: string; delay: number }[] }) {
  return words.map(({ word, delay }, i) => (
    <span key={i} className="inline-block animate-stream" style={{ animationDelay: `${delay}ms` }}>
      {word}
      {i < words.length - 1 ? " " : null}
    </span>
  ));
}

/**
 * Agent hero, after Mainframe: a warm red field, a felt 3D host on the right
 * and a short, chatty greeting on the left with answers as white pills.
 */
function AgentHero() {
  const lines = timeline();
  const done = lines[lines.length - 1].end;
  const pills: Pill[] = [
    { href: "/book", label: "Book a campaign" },
    { href: "/apply", label: "Apply as a creator" },
    { href: "/campaigns", label: "See open campaigns" },
    { href: "#how-it-works", label: "How it works" },
    siteConfig.contactEmail
      ? { href: `mailto:${siteConfig.contactEmail}`, label: `Email us at ${siteConfig.contactEmail}`, outline: true }
      : { href: "/login", label: "Sign in", outline: true },
  ];

  return (
    <section
      aria-labelledby="agent-title"
      className="texture-noise relative isolate min-h-[100svh] overflow-hidden bg-[radial-gradient(ellipse_90%_70%_at_50%_78%,#f0493c_0%,#d92e24_45%,#b5170f_100%)] text-white sm:bg-[radial-gradient(ellipse_70%_85%_at_70%_45%,#f0493c_0%,#d92e24_45%,#b5170f_100%)]"
    >
      <AgentStage />
      <EchoTalks ms={done - START_MS} />

      <div className="pointer-events-none relative z-10 mx-auto flex min-h-[100svh] max-w-[90rem] flex-col px-5 pt-24 pb-10 sm:justify-center sm:px-8 sm:pt-20 lg:px-[6vw]">
        <div className="pointer-events-auto max-w-[34rem] sm:mt-[6vh]">
          <p className="text-[clamp(1.125rem,0.98rem+0.5vw,1.4rem)] leading-[1.35] tracking-[-0.02em] text-white/75">
            <Words words={lines[0].words} />
          </p>
          <h1
            id="agent-title"
            className="mt-1 text-[clamp(1.125rem,0.98rem+0.5vw,1.4rem)] leading-[1.35] font-normal tracking-[-0.02em] text-white/75"
          >
            <Words words={lines[1].words} />
          </h1>
          <p className="mt-5 text-[clamp(1.125rem,0.98rem+0.5vw,1.4rem)] leading-[1.35] tracking-[-0.02em] text-white">
            <Words words={lines[2].words} />
          </p>
          <GreetingPills pills={pills} startMs={done} />
        </div>
      </div>
      <div data-hero-end aria-hidden className="absolute bottom-0 left-0 h-px w-px" />
    </section>
  );
}

export { AgentHero };
