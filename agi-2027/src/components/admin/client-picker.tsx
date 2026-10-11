"use client";

import { useId, useState } from "react";
import { Popover } from "radix-ui";
import { Check, ChevronsUpDown, Plus, Search } from "lucide-react";

import { fieldControlClass } from "@/components/ui/input";
import { demoCampaigns, demoClients } from "@/lib/campaigns/demo";
import { cn } from "@/lib/utils";
import { BrandTile, brandInitials } from "./brand-tile";

const campaignCount = (clientId: string) => demoCampaigns.filter((campaign) => campaign.clientId === clientId).length;

type Option = { id: string; name: string; meta: string; initials: string; color?: string };

/**
 * Pick the brand a campaign is for, or start a new one. Type to filter,
 * arrows to move, Enter to pick.
 */
export function ClientPicker({
  id,
  value,
  newBrandName,
  onChange,
  invalid,
  "aria-describedby": ariaDescribedBy,
  triggerRef,
}: {
  id: string;
  value: string;
  /** Shown on the trigger while a new brand is being added. */
  newBrandName?: string;
  /** For a new brand, the name typed into the search (if any) comes along. */
  onChange: (clientId: string, typedName?: string) => void;
  invalid?: boolean;
  "aria-describedby"?: string;
  triggerRef?: (node: HTMLButtonElement | null) => void;
}) {
  const listId = useId();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);

  const options: Option[] = [
    ...demoClients
      .filter((client) => `${client.name} ${client.xHandle}`.toLowerCase().includes(query.trim().toLowerCase()))
      .map((client) => {
        const count = campaignCount(client.id);
        return {
          id: client.id,
          name: client.name,
          meta: `${client.xHandle} · ${count} ${count === 1 ? "campaign" : "campaigns"}`,
          initials: client.initials,
          color: client.color,
        };
      }),
    { id: "new", name: query.trim() ? `Add "${query.trim()}" as a new brand` : "Add a new brand", meta: "Name, website, X handle and logo", initials: "" },
  ];
  const activeIndex = Math.min(active, options.length - 1);
  const selected = demoClients.find((client) => client.id === value);

  function choose(option: Option | undefined) {
    if (!option) return;
    onChange(option.id, option.id === "new" ? query.trim() || undefined : undefined);
    setOpen(false);
    setQuery("");
    setActive(0);
  }

  return (
    <Popover.Root
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setQuery("");
      }}
    >
      <Popover.Trigger asChild>
        <button
          ref={triggerRef}
          id={id}
          type="button"
          role="combobox"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-controls={open ? listId : undefined}
          aria-invalid={invalid || undefined}
          aria-describedby={ariaDescribedBy}
          className={cn(fieldControlClass, "flex h-14 cursor-pointer items-center gap-3 px-3 text-left")}
        >
          {selected ? (
            <>
              <BrandTile initials={selected.initials} color={selected.color} />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[15px] font-medium">{selected.name}</span>
                <span className="block truncate text-xs text-muted-foreground">{selected.xHandle}</span>
              </span>
            </>
          ) : value === "new" ? (
            <>
              <BrandTile initials={brandInitials(newBrandName ?? "") || "+"} />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[15px] font-medium">{newBrandName?.trim() || "New brand"}</span>
                <span className="block truncate text-xs text-muted-foreground">Added with this campaign</span>
              </span>
            </>
          ) : (
            <span className="flex-1 text-subtle-foreground">Pick a brand</span>
          )}
          <ChevronsUpDown className="size-4 shrink-0 text-muted-foreground" aria-hidden />
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="start"
          sideOffset={6}
          className="z-50 w-(--radix-popover-trigger-width) min-w-72 overflow-hidden rounded-xl border border-border-strong bg-popover p-1.5 text-popover-foreground shadow-2xl outline-none data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-[0.98]"
        >
          <div className="flex items-center gap-2 border-b px-2 pb-1.5">
            <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setActive(0);
              }}
              onKeyDown={(event) => {
                if (event.key === "ArrowDown") {
                  event.preventDefault();
                  setActive((activeIndex + 1) % options.length);
                } else if (event.key === "ArrowUp") {
                  event.preventDefault();
                  setActive((activeIndex - 1 + options.length) % options.length);
                } else if (event.key === "Enter") {
                  event.preventDefault();
                  choose(options[activeIndex]);
                }
              }}
              placeholder="Search brands"
              role="combobox"
              aria-expanded="true"
              aria-controls={listId}
              aria-activedescendant={`${listId}-${activeIndex}`}
              aria-label="Search brands"
              className="h-10 min-w-0 flex-1 bg-transparent text-base outline-none placeholder:text-subtle-foreground sm:text-sm"
            />
          </div>
          <ul id={listId} role="listbox" aria-label="Brands" className="max-h-72 overflow-y-auto pt-1.5">
            {options.map((option, index) => {
              const isNew = option.id === "new";
              const isSelected = option.id === value;
              return (
                <li
                  key={option.id}
                  id={`${listId}-${index}`}
                  role="option"
                  aria-selected={isSelected}
                  onMouseMove={() => setActive(index)}
                  onClick={() => choose(option)}
                  className={cn(
                    "flex min-h-12 cursor-pointer items-center gap-3 rounded-lg px-2 py-1.5",
                    index === activeIndex && "bg-surface-2",
                    isNew && "mt-1 border-t pt-2",
                  )}
                >
                  {isNew ? (
                    <span className="flex size-9 shrink-0 items-center justify-center rounded-[30%] border border-dashed border-border-strong text-muted-foreground">
                      <Plus className="size-4" aria-hidden />
                    </span>
                  ) : (
                    <BrandTile initials={option.initials} color={option.color} />
                  )}
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium">{option.name}</span>
                    <span className="block truncate text-xs text-muted-foreground">{option.meta}</span>
                  </span>
                  {isSelected ? <Check className="size-4 shrink-0 text-foreground" aria-hidden /> : null}
                </li>
              );
            })}
          </ul>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
