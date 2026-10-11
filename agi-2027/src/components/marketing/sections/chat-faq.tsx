"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { AnimatePresence, motion, useInView, useReducedMotion } from "motion/react";

type Faq = { question: string; answer: string };
type Message = { id: number; from: "echo" | "you"; text: string };

/**
 * Agent look: the FAQ as a chat with Echo. Tap a question and Echo types the
 * answer. New messages are announced to screen readers.
 */
function ChatFaq({ faqs }: { faqs: Faq[] }) {
  const reduce = useReducedMotion();
  const [messages, setMessages] = useState<Message[]>([
    { id: 0, from: "echo", text: "Ask me anything. These are the questions people ask most." },
  ]);
  const [typing, setTyping] = useState(false);
  const [asked, setAsked] = useState<string[]>([]);
  const log = useRef<HTMLDivElement>(null);
  const host = useRef<HTMLDivElement>(null);
  const nextId = useRef(1);
  const inView = useInView(host, { once: true, amount: 0.6 });

  useEffect(() => {
    const element = log.current;
    if (element) element.scrollTo({ top: element.scrollHeight, behavior: reduce ? "auto" : "smooth" });
  }, [messages, typing, reduce]);

  function ask(faq: Faq) {
    if (typing) return;
    setAsked((current) => [...current, faq.question]);
    setMessages((current) => [...current, { id: nextId.current++, from: "you", text: faq.question }]);
    setTyping(true);
    window.dispatchEvent(new CustomEvent("agi:echo", { detail: { mood: "talk", ms: 1400 } }));
    window.setTimeout(
      () => {
        setTyping(false);
        setMessages((current) => [...current, { id: nextId.current++, from: "echo", text: faq.answer }]);
      },
      reduce ? 0 : 750,
    );
  }

  // Show how it works: the first question asks itself when the chat comes into view.
  const started = useRef(false);
  useEffect(() => {
    if (!inView || started.current || !faqs[0]) return;
    started.current = true;
    const timer = window.setTimeout(() => ask(faqs[0]), 700);
    return () => window.clearTimeout(timer);
    // ask() only reads state through setters; running once is the point.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inView]);

  const remaining = faqs.filter((faq) => !asked.includes(faq.question));

  return (
    <div ref={host} className="flex h-[34rem] flex-col overflow-hidden rounded-[2rem] bg-surface shadow-float ring-1 ring-border">
      <div className="flex items-center gap-3 border-b px-5 py-4">
        <Image src="/art/echo-avatar.webp" alt="" width={40} height={40} className="size-10 rounded-full bg-[#d92e24]" />
        <div className="leading-tight">
          <p className="text-[15px] font-semibold">Echo</p>
          <p className="text-[13px] text-muted-foreground">Answers in a second</p>
        </div>
      </div>

      <div ref={log} role="log" aria-live="polite" className="flex flex-1 flex-col gap-2.5 overflow-y-auto px-4 py-5 [scrollbar-width:thin]">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.p
              key={message.id}
              layout={!reduce}
              initial={reduce ? { opacity: 0 } : { opacity: 0, y: 12, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className={
                message.from === "you"
                  ? "max-w-[85%] self-end rounded-[1.3rem] rounded-br-md bg-brand px-4 py-2.5 text-[15px] leading-snug text-brand-foreground"
                  : "max-w-[85%] self-start rounded-[1.3rem] rounded-bl-md bg-surface-2 px-4 py-2.5 text-[15px] leading-relaxed"
              }
              style={{ transformOrigin: message.from === "you" ? "bottom right" : "bottom left" }}
            >
              {message.text}
            </motion.p>
          ))}
          {typing ? (
            <motion.span
              key="typing"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex w-fit gap-1 self-start rounded-full bg-surface-2 px-4 py-3"
              aria-label="Echo is typing"
            >
              {[0, 1, 2].map((dot) => (
                <span key={dot} className="size-1.5 animate-pulse rounded-full bg-muted-foreground" style={{ animationDelay: `${dot * 160}ms` }} />
              ))}
            </motion.span>
          ) : null}
        </AnimatePresence>
      </div>

      <div className="border-t bg-surface-2/60 px-4 py-3">
        {remaining.length ? (
          <ul className="flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none]" aria-label="Questions you can ask">
            {remaining.map((faq) => (
              <li key={faq.question} className="shrink-0">
                <button
                  type="button"
                  onClick={() => ask(faq)}
                  disabled={typing}
                  className="pressable h-10 cursor-pointer rounded-full bg-surface px-4 text-[14px] font-medium ring-1 ring-border-strong transition-colors hover:bg-foreground hover:text-background disabled:opacity-50"
                >
                  {faq.question}
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="py-2 text-center text-[14px] text-muted-foreground">
            That&apos;s everything. Book a campaign and we&apos;ll talk it through.
          </p>
        )}
      </div>
    </div>
  );
}

export { ChatFaq };
