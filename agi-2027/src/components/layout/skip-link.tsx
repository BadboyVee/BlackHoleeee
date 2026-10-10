/** First focusable element on every page: jumps keyboard users past the navigation. */
function SkipLink() {
  return (
    <a
      href="#main"
      className="fixed top-3 left-3 z-[60] -translate-y-20 rounded-full bg-foreground px-4 py-2.5 text-sm font-medium text-background shadow-lg transition-transform focus-visible:translate-y-0"
    >
      Skip to content
    </a>
  );
}

export { SkipLink };
