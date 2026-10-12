import type { ReactNode } from "react";

import { excerptPost, splitPostText, type ShowcasePost } from "@/lib/showcase-posts";
import { cn } from "@/lib/utils";

/*
 * The pieces of a real X post, shared by the Drop hero's phone and the proof
 * cards. No hooks, so they render on the server and inside client components.
 */

/**
 * X's verified badge: gold for businesses, blue for everyone else. Solid
 * fills, no gradient: a url(#id) gradient breaks when its first copy sits in
 * a look that's hidden.
 */
function VerifiedBadge({ badge, className }: { badge: ShowcasePost["author"]["badge"]; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-label={badge === "gold" ? "Verified organization" : "Verified"} role="img" className={className}>
      <path
        fill={badge === "gold" ? "#e2a40e" : "#1d9bf0"}
        d="M12 1.5l2.6 1.9 3.2-.2 1 3 2.6 1.9-1 3 1 3-2.6 1.9-1 3-3.2-.2L12 22.5l-2.6-1.9-3.2.2-1-3-2.6-1.9 1-3-1-3 2.6-1.9 1-3 3.2.2z"
      />
      <path d="M10.4 15.6l-3.2-3.2 1.4-1.4 1.8 1.8 4.9-4.9 1.4 1.4z" fill={badge === "gold" ? "#000" : "#fff"} />
    </svg>
  );
}

function PostAvatar({ author, className }: { author: ShowcasePost["author"]; className?: string }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element -- tiny, and the phone preloads the same URL
    <img
      src={author.avatar}
      alt=""
      width={128}
      height={128}
      decoding="async"
      className={cn(
        "shrink-0 object-cover",
        author.avatarShape === "circle" ? "rounded-full" : "rounded-[22%]",
        className,
      )}
    />
  );
}

/**
 * The post's words, cut to `max` characters for tight spots, with mentions,
 * hashtags and bare links in the accent color. `more` follows a cut text.
 */
function PostText({
  post,
  max,
  className,
  accentClassName,
  more,
}: {
  post: ShowcasePost;
  max: number;
  className?: string;
  accentClassName?: string;
  more?: ReactNode;
}) {
  const { text, cut } = excerptPost(post.text, max);
  return (
    <p className={cn("whitespace-pre-line", className)}>
      {splitPostText(text, post.links).map((part, i) =>
        part.kind === "text" ? (
          part.text
        ) : (
          <span key={i} className={accentClassName}>
            {part.text}
          </span>
        ),
      )}
      {cut ? more : null}
    </p>
  );
}

export { PostAvatar, PostText, VerifiedBadge };
