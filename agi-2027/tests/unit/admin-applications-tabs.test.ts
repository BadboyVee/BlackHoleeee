import { describe, expect, it } from "vitest";

import {
  applicationTabFrom,
  applicationTabHref,
  rowsForTab,
  tabCounts,
} from "@/components/admin/applications/tabs";
import { demoApplications } from "@/lib/creators/demo";

const ids = (rows: { id: string }[]) => rows.map((row) => row.id);

describe("admin application tabs", () => {
  it("counts each tab", () => {
    expect(tabCounts(demoApplications)).toEqual({ waiting: 2, approved: 2, rejected: 1, all: 5 });
    expect(tabCounts([])).toEqual({ waiting: 0, approved: 0, rejected: 0, all: 0 });
  });

  it("lists Waiting oldest first, so nobody waits longest", () => {
    expect(ids(rowsForTab(demoApplications, "waiting"))).toEqual(["demo-app-2", "demo-app-1"]);
  });

  it("lists decisions latest first, and All newest first", () => {
    expect(ids(rowsForTab(demoApplications, "approved"))).toEqual(["demo-app-3", "demo-app-4"]);
    expect(ids(rowsForTab(demoApplications, "rejected"))).toEqual(["demo-app-5"]);
    expect(ids(rowsForTab(demoApplications, "all"))).toEqual(["demo-app-1", "demo-app-2", "demo-app-3", "demo-app-4", "demo-app-5"]);
  });

  it("keeps an application decided just now in Waiting until the tab changes", () => {
    const decided = demoApplications.map((row) => (row.id === "demo-app-2" ? { ...row, status: "approved" as const } : row));
    expect(ids(rowsForTab(decided, "waiting"))).toEqual(["demo-app-1"]);
    expect(ids(rowsForTab(decided, "waiting", new Set(["demo-app-2"])))).toEqual(["demo-app-2", "demo-app-1"]);
  });

  it("reads the tab from the address, and writes it back", () => {
    expect(applicationTabFrom("approved")).toBe("approved");
    expect(applicationTabFrom("nope")).toBe("waiting");
    expect(applicationTabFrom(null)).toBe("waiting");
    expect(applicationTabHref("/admin/applications", "waiting")).toBe("/admin/applications");
    expect(applicationTabHref("/admin/applications", "all")).toBe("/admin/applications?status=all");
  });
});
