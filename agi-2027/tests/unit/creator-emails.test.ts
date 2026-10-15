import { describe, expect, it } from "vitest";

import {
  applicationApprovedEmail,
  applicationReceivedEmail,
  applicationRejectedEmail,
  payoutDetailsChangedEmail,
  type ApplicationEmailData,
} from "@/lib/email/creator-emails";
import { renderEmail } from "@/lib/email/layout";

const DASHES = /[–—]/;
const site = { siteUrl: "https://agi2027.example/", contactEmail: "hi@agi2027.example" };

const application: ApplicationEmailData = {
  createdAt: "2026-10-13T14:05:00Z",
  bestPosts: ["https://x.com/amarabuilds/status/1", "https://x.com/amarabuilds/status/2"],
  why: "I review AI tools\nevery week.",
  applicant: {
    displayName: "Amara Okafor",
    email: "amara@example.com",
    xHandle: "amarabuilds",
    followers: 18400,
    avgViews: 6200,
    niches: ["ai", "dev_tools"],
    country: "NG",
    tiktokUrl: null,
    youtubeUrl: "https://youtube.com/@amara",
    instagramUrl: null,
    linkedinUrl: null,
  },
  referrer: { displayName: "Tolu Ade", xHandle: "tolu" },
};

describe("applicationReceivedEmail", () => {
  it("gives the owner everything needed to decide, with a link to review", () => {
    const email = applicationReceivedEmail(application, site);
    expect(email.subject).toBe("New creator application: Amara Okafor (@amarabuilds)");
    for (const piece of [
      "Followers: 18,400",
      "Views per post: 6,200",
      "Niches: AI, Dev tools",
      "Country: Nigeria",
      "https://x.com/amarabuilds/status/2",
      "Referred by: Tolu Ade (@tolu)",
      "Applied: 13 Oct 2026, 14:05 UTC",
      "Review applications: https://agi2027.example/admin/applications",
    ]) {
      expect(email.text).toContain(piece);
    }
    expect(email.html).toContain('href="https://x.com/amarabuilds"');
    expect(email.html).toContain("I review AI tools<br>every week.");
  });

  it("leaves out what the applicant didn't give", () => {
    const email = applicationReceivedEmail(
      { ...application, referrer: null, applicant: { ...application.applicant, youtubeUrl: null, country: null } },
      site,
    );
    expect(email.text).not.toContain("Referred by");
    expect(email.text).not.toContain("YouTube");
    expect(email.text).not.toContain("Country");
  });

  it("escapes whatever the applicant typed", () => {
    const email = applicationReceivedEmail(
      { ...application, why: "<script>alert(1)</script>", applicant: { ...application.applicant, displayName: '<img src=x onerror="y">' } },
      site,
    );
    expect(email.html).not.toContain("<script>");
    expect(email.html).not.toContain("<img");
    expect(email.html).toContain("&lt;script&gt;");
  });
});

describe("applicationApprovedEmail", () => {
  it("welcomes them, points to the dashboard and shares their referral link", () => {
    const email = applicationApprovedEmail({ displayName: "Amara Okafor", referralCode: "9f3a1c2b", viaInvite: false }, site);
    expect(email.subject).toBe("You're in: welcome to AGI 2027");
    expect(email.text).toContain("Hi Amara, good news: your application is approved.");
    expect(email.text).toContain("https://agi2027.example/apply?ref=9f3a1c2b");
    expect(email.text).toContain("Open your dashboard: https://agi2027.example/dashboard");
    expect(email.text).toContain("add your payout details");
  });

  it("says the invite worked when they came through one", () => {
    const email = applicationApprovedEmail({ displayName: "Amara", referralCode: null, viaInvite: true }, site);
    expect(email.text).toContain("Your invite worked");
    expect(email.text).not.toContain("apply?ref=");
  });
});

describe("applicationRejectedEmail", () => {
  it("is kind and gives no reasons", () => {
    const email = applicationRejectedEmail({ displayName: "Amara Okafor" }, site);
    expect(email.subject).toBe("About your AGI 2027 application");
    expect(email.text).toContain("Hi Amara, thanks for applying");
    expect(email.text).toContain("hi@agi2027.example");
  });
});

describe("payoutDetailsChangedEmail", () => {
  it("shows the masked new details and what to do if it wasn't them", () => {
    const email = payoutDetailsChangedEmail({ displayName: "Amara", summary: "USDC on Base, wallet ending 9EE7" }, site);
    expect(email.subject).toBe("Your payout details changed");
    expect(email.text).toContain("Now paying to: USDC on Base, wallet ending 9EE7");
    expect(email.text).toContain("If it wasn't you, tell us straight away");
    expect(email.text).toContain("https://agi2027.example/dashboard/profile");
  });
});

describe("every email", () => {
  it("never uses dashes, per the copy rules", () => {
    const emails = [
      applicationReceivedEmail(application, site),
      applicationApprovedEmail({ displayName: "A", referralCode: "9f3a1c2b", viaInvite: false }, site),
      applicationApprovedEmail({ displayName: "A", referralCode: null, viaInvite: true }, site),
      applicationRejectedEmail({ displayName: "A" }, site),
      payoutDetailsChangedEmail({ displayName: "A", summary: "x" }, site),
    ];
    for (const email of emails) {
      expect(email.subject).not.toMatch(DASHES);
      expect(email.text, email.subject).not.toMatch(DASHES);
    }
  });

  it("drops the contact line's address when there is none", () => {
    expect(applicationRejectedEmail({ displayName: "A" }, { contactEmail: "" }).text).toContain("Questions?");
  });

  it("escapes button links and keeps the plain text readable", () => {
    const email = renderEmail({
      subject: "S",
      heading: "H",
      paragraphs: ["P"],
      button: { label: "Go", href: 'https://x.example/?a=1&b="2"' },
    });
    expect(email.html).toContain('href="https://x.example/?a=1&amp;b=&quot;2&quot;"');
    expect(email.text).toBe('H\n\nP\n\nGo: https://x.example/?a=1&b="2"');
  });
});
