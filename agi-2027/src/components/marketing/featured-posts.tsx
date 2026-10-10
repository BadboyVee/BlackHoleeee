import { Eye, Heart, Repeat2 } from "lucide-react";

import { XLogo } from "@/components/brand/social-icons";
import { featuredPosts, type FeaturedPost } from "@/lib/marketing-content";
import { Section, SectionHeader } from "./section";

const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

function PostCard({ post }: { post: FeaturedPost }) {
  const { creator, metrics } = post;
  return (
    <article className="relative flex w-[86%] shrink-0 snap-center flex-col rounded-2xl border bg-surface p-5 shadow-soft sm:w-auto sm:p-6">
      <header className="flex items-center gap-3">
        <div
          aria-hidden
          className="flex size-10 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold text-white"
          style={{
            background: `linear-gradient(140deg, hsl(${creator.hue} 32% 58%), hsl(${creator.hue + 30} 30% 28%))`,
          }}
        >
          {creator.initials}
        </div>
        <div className="min-w-0">
          <p className="truncate text-[15px] font-semibold tracking-[-0.015em]">{creator.name}</p>
          <p className="truncate text-sm text-subtle-foreground">@{creator.handle}</p>
        </div>
        <XLogo className="ml-auto size-4 shrink-0 text-muted-foreground" />
      </header>

      <p className="mt-4 flex-1 text-[15px] leading-relaxed text-pretty">{post.text}</p>
      <p className="mt-4 text-xs text-subtle-foreground">
        Paid partnership · {post.brand}, {post.moment.toLowerCase()}
      </p>

      <footer className="mt-4 flex items-center gap-4 border-t pt-4 text-[13px] text-muted-foreground">
        <span className="inline-flex items-center gap-1.5 tabular" title="Views">
          <Eye className="size-3.5" aria-hidden />
          <span className="sr-only">Views</span>
          {compact.format(metrics.views)}
        </span>
        <span className="inline-flex items-center gap-1.5 tabular" title="Likes">
          <Heart className="size-3.5" aria-hidden />
          <span className="sr-only">Likes</span>
          {compact.format(metrics.likes)}
        </span>
        <span className="inline-flex items-center gap-1.5 tabular" title="Reposts">
          <Repeat2 className="size-3.5" aria-hidden />
          <span className="sr-only">Reposts</span>
          {compact.format(metrics.reposts)}
        </span>
      </footer>
    </article>
  );
}

function FeaturedPosts() {
  return (
    <Section id="proof">
      <SectionHeader
        kicker="Proof"
        title="Posts that *moved* launches."
        description="Every campaign ends with the numbers: views, likes, reposts and replies, post by post."
      />
      <div className="-mx-5 mt-14 flex snap-x snap-mandatory gap-4 overflow-x-auto px-5 pb-2 [scrollbar-width:none] sm:mx-0 sm:grid sm:grid-cols-2 sm:overflow-visible sm:px-0 lg:grid-cols-3">
        {featuredPosts.map((post) => (
          <PostCard key={post.creator.handle} post={post} />
        ))}
      </div>
    </Section>
  );
}

export { FeaturedPosts };
