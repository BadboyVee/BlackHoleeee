"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Ellipsis, LogOut, Pause, Pencil, Copy, Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Field, fieldDescribedBy } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function FormDemo() {
  const [handle, setHandle] = useState("");
  const handleError =
    handle && !/^@?[A-Za-z0-9_]{1,15}$/.test(handle) ? "X handles use letters, numbers and underscores, up to 15." : undefined;

  return (
    <div className="grid gap-6 sm:grid-cols-2">
      <Field id="sg-name" label="Display name" hint="How you appear to the agency.">
        <Input id="sg-name" placeholder="Ada Lovelace" aria-describedby={fieldDescribedBy("sg-name", { hint: true })} />
      </Field>
      <Field id="sg-handle" label="X handle" error={handleError} hint="Type something with a space to see the error state.">
        <Input
          id="sg-handle"
          placeholder="@yourhandle"
          value={handle}
          onChange={(event) => setHandle(event.target.value)}
          aria-invalid={Boolean(handleError) || undefined}
          aria-describedby={fieldDescribedBy("sg-handle", { hint: true, error: handleError })}
        />
      </Field>
      <Field id="sg-niche" label="Main niche">
        <Select>
          <SelectTrigger id="sg-niche">
            <SelectValue placeholder="Pick one" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ai">AI</SelectItem>
            <SelectItem value="tech">Tech</SelectItem>
            <SelectItem value="crypto">Crypto</SelectItem>
            <SelectItem value="startups">Startups</SelectItem>
            <SelectItem value="design">Design</SelectItem>
          </SelectContent>
        </Select>
      </Field>
      <Field id="sg-followers" label="Followers on X" optional>
        <Input id="sg-followers" inputMode="numeric" placeholder="25,000" />
      </Field>
      <Field id="sg-why" label="Why do you want to join?" className="sm:col-span-2">
        <Textarea id="sg-why" placeholder="Tell us about your audience and the kind of launches you love covering." />
      </Field>
      <div className="flex items-start gap-3 sm:col-span-2">
        <Checkbox id="sg-label" defaultChecked />
        <Label htmlFor="sg-label" className="leading-snug font-normal">
          I used X&apos;s paid partnership label and followed the brief.
        </Label>
      </div>
      <div className="flex items-center justify-between gap-4 rounded-xl border px-4 py-3 sm:col-span-2">
        <Label htmlFor="sg-email-drops" className="flex-col items-start gap-1">
          <span>Email me about new drops</span>
          <span className="text-[13px] font-normal text-muted-foreground">Payment emails always send.</span>
        </Label>
        <Switch id="sg-email-drops" defaultChecked />
      </div>
    </div>
  );
}

export function FeedbackDemo() {
  return (
    <div className="flex flex-wrap gap-2">
      <Button variant="secondary" onClick={() => toast.success("Proof approved", { description: "Ada's post on Nebula 2.0 is approved. An earning was created." })}>
        Success toast
      </Button>
      <Button variant="secondary" onClick={() => toast("Campaign dropped", { description: "20 creators were notified by email and Telegram." })}>
        Info toast
      </Button>
      <Button variant="secondary" onClick={() => toast.error("That link was already submitted", { description: "Each post can only be used as proof once." })}>
        Error toast
      </Button>
    </div>
  );
}

export function OverlayDemo() {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="secondary">Open dialog</Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Drop this claim?</DialogTitle>
            <DialogDescription>
              Your slot opens up for another creator. You can&apos;t claim this campaign again
              yourself.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="ghost">Keep my slot</Button>
            </DialogClose>
            <DialogClose asChild>
              <Button variant="destructive">Drop claim</Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Sheet>
        <SheetTrigger asChild>
          <Button variant="secondary">Open sheet</Button>
        </SheetTrigger>
        <SheetContent side="right">
          <SheetHeader>
            <SheetTitle>Filters</SheetTitle>
            <SheetDescription>Sheets slide in from the edge, which suits phones.</SheetDescription>
          </SheetHeader>
        </SheetContent>
      </Sheet>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="secondary" size="icon" aria-label="Campaign actions">
            <Ellipsis />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuLabel>Campaign</DropdownMenuLabel>
          <DropdownMenuItem>
            <Pencil />
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Copy />
            Duplicate
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Pause />
            Pause
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem variant="destructive">
            <LogOut />
            Close campaign
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="What is a slot?">
            <Info />
          </Button>
        </TooltipTrigger>
        <TooltipContent>A slot is one creator&apos;s place on a campaign.</TooltipContent>
      </Tooltip>
    </div>
  );
}

export function TabsDemo() {
  return (
    <Tabs defaultValue="active">
      <TabsList>
        <TabsTrigger value="active">Active</TabsTrigger>
        <TabsTrigger value="submitted">Submitted</TabsTrigger>
        <TabsTrigger value="approved">Approved</TabsTrigger>
        <TabsTrigger value="paid">Paid</TabsTrigger>
        <TabsTrigger value="past">Past</TabsTrigger>
      </TabsList>
      <TabsContent value="active" className="text-sm text-muted-foreground">
        Claims you&apos;re working on, with countdowns to your post time.
      </TabsContent>
      <TabsContent value="submitted" className="text-sm text-muted-foreground">
        Drafts and proof waiting on the agency.
      </TabsContent>
      <TabsContent value="approved" className="text-sm text-muted-foreground">
        Approved posts with payment on the way.
      </TabsContent>
      <TabsContent value="paid" className="text-sm text-muted-foreground">
        Paid, with references.
      </TabsContent>
      <TabsContent value="past" className="text-sm text-muted-foreground">
        Expired and cancelled claims.
      </TabsContent>
    </Tabs>
  );
}
