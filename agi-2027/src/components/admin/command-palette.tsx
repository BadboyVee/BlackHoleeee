"use client";

import { createContext, useCallback, useContext, useEffect, useId, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Dialog as DialogPrimitive } from "radix-ui";
import { ArrowRight, CornerDownLeft, Copy, Moon, Plus, Search } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { clientById, demoCampaigns } from "@/lib/campaigns/demo";
import { showSampleData } from "@/lib/sample-data";
import { applyTheme, currentTheme, storeTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { adminNavGroups, type AdminNavItem } from "./admin-nav";
import { BrandTile } from "./brand-tile";
import { Kbd } from "./kbd";

type CommandItem = {
  id: string;
  group: "Actions" | "Pages" | "Campaigns";
  label: string;
  hint?: string;
  keywords: string;
  render: "action" | "page" | "campaign";
  icon?: AdminNavItem["icon"];
  campaignId?: string;
  run: (router: ReturnType<typeof useRouter>) => void;
};

const CommandContext = createContext<{ openPalette: () => void }>({ openPalette: () => {} });

export function useCommandPalette() {
  return useContext(CommandContext);
}

/**
 * Everything search can reach. Sample campaigns, and the builder actions that
 * only save on preview links, are left out when showSamples is false (the
 * live site).
 */
export function buildItems(showSamples: boolean): CommandItem[] {
  const sampleActions: CommandItem[] = [
    {
      id: "action-new",
      group: "Actions",
      label: "New campaign",
      hint: "Open the campaign builder",
      keywords: "create add list launch",
      render: "action",
      icon: Plus,
      run: (router) => router.push("/admin/campaigns/new"),
    },
    {
      id: "action-duplicate",
      group: "Actions",
      label: "Duplicate Nebula 2.0 launch day",
      hint: "Start a rerun with the same brief",
      keywords: "copy rerun again",
      render: "action",
      icon: Copy,
      run: (router) => router.push("/admin/campaigns/new?from=cmp-nebula-2"),
    },
  ];
  const actions: CommandItem[] = [
    ...(showSamples ? sampleActions : []),
    {
      id: "action-theme",
      group: "Actions",
      label: "Switch light or dark mode",
      keywords: "theme dark light appearance",
      render: "action",
      icon: Moon,
      run: () => {
        const next = currentTheme() === "dark" ? "light" : "dark";
        storeTheme(next);
        applyTheme(next);
      },
    },
  ];
  const pages: CommandItem[] = adminNavGroups.flatMap((group) =>
    group.items.map((item) => ({
      id: `page-${item.href}`,
      group: "Pages" as const,
      label: item.label,
      hint: group.label,
      keywords: `${item.keywords ?? ""} ${group.label}`,
      render: "page" as const,
      icon: item.icon,
      run: (router: ReturnType<typeof useRouter>) => router.push(item.href),
    })),
  );
  const campaigns: CommandItem[] = (showSamples ? demoCampaigns : []).map((campaign) => {
    const client = clientById(campaign.clientId);
    return {
      id: `campaign-${campaign.id}`,
      group: "Campaigns" as const,
      label: campaign.title,
      hint: client?.name,
      keywords: `${client?.name ?? ""} ${campaign.status} ${campaign.summary}`,
      render: "campaign" as const,
      campaignId: campaign.id,
      run: (router: ReturnType<typeof useRouter>) => router.push(`/admin/campaigns/${campaign.id}`),
    };
  });
  return [...actions, ...pages, ...campaigns];
}

const COMMAND_ITEMS = buildItems(showSampleData());

function matches(item: CommandItem, query: string) {
  const haystack = `${item.label} ${item.hint ?? ""} ${item.keywords}`.toLowerCase();
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((word) => haystack.includes(word));
}

function isTypingTarget(target: EventTarget | null) {
  const el = target as HTMLElement | null;
  if (!el) return false;
  return el.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName);
}

/** Holds the palette and listens for ⌘K / Ctrl K anywhere in the admin. */
export function CommandPaletteProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        // Let ⌘K inside a text field still open search; it has no other meaning there.
        event.preventDefault();
        setOpen((value) => !value);
        return;
      }
      if (event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey && !isTypingTarget(event.target)) {
        event.preventDefault();
        setOpen(true);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const value = useMemo(() => ({ openPalette: () => setOpen(true) }), []);

  return (
    <CommandContext.Provider value={value}>
      {children}
      <CommandPalette open={open} onOpenChange={setOpen} />
    </CommandContext.Provider>
  );
}

function CommandPalette({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const router = useRouter();
  const listId = useId();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const results = useMemo(() => COMMAND_ITEMS.filter((item) => matches(item, query)), [query]);
  const activeIndex = Math.min(active, Math.max(results.length - 1, 0));

  const close = useCallback(
    (next: boolean) => {
      onOpenChange(next);
      if (!next) {
        setQuery("");
        setActive(0);
      }
    },
    [onOpenChange],
  );

  function choose(item: CommandItem | undefined) {
    if (!item) return;
    close(false);
    item.run(router);
  }

  function move(delta: number) {
    if (results.length === 0) return;
    const next = (activeIndex + delta + results.length) % results.length;
    setActive(next);
    document.getElementById(`${listId}-${next}`)?.scrollIntoView({ block: "nearest" });
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      move(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      move(-1);
    } else if (event.key === "Home") {
      event.preventDefault();
      setActive(0);
    } else if (event.key === "End") {
      event.preventDefault();
      setActive(Math.max(results.length - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      choose(results[activeIndex]);
    }
  }

  return (
    <DialogPrimitive.Root open={open} onOpenChange={close}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-overlay backdrop-blur-[2px] data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:duration-150" />
        <DialogPrimitive.Content
          aria-describedby={undefined}
          className={cn(
            "fixed inset-x-3 top-3 z-50 mx-auto flex max-h-[calc(100dvh-1.5rem)] max-w-[38rem] flex-col overflow-hidden rounded-2xl border border-border-strong bg-popover text-popover-foreground shadow-2xl outline-none sm:top-[12vh] sm:max-h-[70vh]",
            "data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-[0.98] data-[state=open]:slide-in-from-top-2 data-[state=open]:duration-150",
            "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-[0.98] data-[state=closed]:duration-100",
          )}
        >
          <DialogPrimitive.Title className="sr-only">Search and jump</DialogPrimitive.Title>
          <div className="flex items-center gap-3 border-b px-4">
            <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setActive(0);
              }}
              onKeyDown={onKeyDown}
              placeholder="Search pages and campaigns, or type an action"
              role="combobox"
              aria-expanded="true"
              aria-controls={listId}
              aria-activedescendant={results.length ? `${listId}-${activeIndex}` : undefined}
              aria-autocomplete="list"
              className="h-14 min-w-0 flex-1 bg-transparent text-base outline-none placeholder:text-subtle-foreground sm:text-[15px]"
            />
            <Kbd className="hidden sm:inline-flex">Esc</Kbd>
          </div>

          <div id={listId} role="listbox" aria-label="Results" className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-2">
            {results.length === 0 ? (
              <p className="px-3 py-10 text-center text-sm text-muted-foreground">
                Nothing matches &ldquo;{query}&rdquo;. Try a campaign or a brand name.
              </p>
            ) : null}
            {results.map((item, index) => {
              const showGroup = index === 0 || results[index - 1]?.group !== item.group;
              const selected = index === activeIndex;
              return (
                <div key={item.id}>
                  {showGroup ? (
                    <p className="px-3 pt-3 pb-1.5 text-label text-subtle-foreground first:pt-1" role="presentation">
                      {item.group}
                    </p>
                  ) : null}
                  <div
                    id={`${listId}-${index}`}
                    role="option"
                    aria-selected={selected}
                    onMouseMove={() => {
                      if (!selected) setActive(index);
                    }}
                    onClick={() => choose(item)}
                    className={cn(
                      "flex min-h-11 cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm",
                      selected ? "bg-surface-2 text-foreground" : "text-foreground/90",
                    )}
                  >
                    <CommandIcon item={item} />
                    <span className="min-w-0 flex-1 truncate font-medium">{item.label}</span>
                    {item.render === "campaign" && item.campaignId ? <CampaignStatus id={item.campaignId} /> : null}
                    {item.hint && item.render !== "campaign" ? (
                      <span className="hidden truncate text-xs text-muted-foreground sm:block">{item.hint}</span>
                    ) : null}
                    {selected ? <CornerDownLeft className="size-3.5 shrink-0 text-muted-foreground" aria-hidden /> : null}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="hidden items-center gap-4 border-t px-4 py-2.5 text-xs text-muted-foreground sm:flex">
            <span className="inline-flex items-center gap-1.5">
              <Kbd>↑</Kbd>
              <Kbd>↓</Kbd>
              to move
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Kbd>Enter</Kbd>
              to open
            </span>
            <span className="ml-auto inline-flex items-center gap-1.5">
              <ArrowRight className="size-3" aria-hidden />
              Press <Kbd>/</Kbd> anywhere to search
            </span>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}

function CommandIcon({ item }: { item: CommandItem }) {
  if (item.render === "campaign" && item.campaignId) {
    const campaign = demoCampaigns.find((entry) => entry.id === item.campaignId);
    const client = campaign ? clientById(campaign.clientId) : undefined;
    return <BrandTile initials={client?.initials ?? "?"} color={client?.color} size="xs" />;
  }
  const Icon = item.icon;
  return (
    <span className="flex size-6 shrink-0 items-center justify-center rounded-md border bg-surface text-muted-foreground">
      {Icon ? <Icon className="size-3.5" aria-hidden /> : null}
    </span>
  );
}

function CampaignStatus({ id }: { id: string }) {
  const campaign = demoCampaigns.find((entry) => entry.id === id);
  return campaign ? <StatusBadge kind="campaign" status={campaign.status} className="shrink-0" /> : null;
}
