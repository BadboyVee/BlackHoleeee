import { describe, expect, it } from "vitest";

import { COUNTRIES, countryName, isCountryCode } from "@/lib/creators/countries";
import { assetOnNetwork, CRYPTO_NETWORKS, isWalletAddress, NICHES } from "@/lib/creators/options";
import {
  applicationSchema,
  inviteSchema,
  normalizeSocialLink,
  parseCount,
  payoutSchema,
  profileSchema,
  type ApplicationInput,
} from "@/lib/creators/schemas";

const EVM = "0x52908400098527886E0F7030069857D2E4169EE7";
const SOLANA = "7EYnhQoR9YM3N7UoaKRoA44Uy8JeaZV3qyouov87awMs";
const TRON = "TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy";

const application: ApplicationInput = {
  displayName: " Amara Okafor ",
  xHandle: "@AmaraBuilds",
  tiktok: "",
  youtube: "youtube.com/@amara",
  instagram: undefined,
  linkedin: "https://www.linkedin.com/in/amara/",
  niches: ["ai", "startups", "ai"],
  followers: "18.4k",
  avgViews: "6,200",
  country: "ng",
  bestPosts: ["x.com/amarabuilds/status/1", "https://x.com/amarabuilds/status/2", "https://twitter.com/amarabuilds/status/3"],
  why: "I review AI tools every week for founders who build in public.",
  referralCode: " 9F3A1C2B ",
};

function errorsOf(result: { success: boolean; error?: { issues: { path: PropertyKey[]; message: string }[] } }) {
  return Object.fromEntries((result.error?.issues ?? []).map((issue) => [issue.path.join("."), issue.message]));
}

describe("parseCount", () => {
  it("reads the ways creators write numbers", () => {
    expect(parseCount("18400")).toBe(18400);
    expect(parseCount("18,400")).toBe(18400);
    expect(parseCount("18 400")).toBe(18400);
    expect(parseCount("18.4k")).toBe(18400);
    expect(parseCount("1.2M")).toBe(1200000);
    expect(parseCount("0")).toBe(0);
  });

  it("refuses anything else", () => {
    for (const value of ["", "lots", "-5", "1e9", "12.4.5", "3000000000", "k"]) expect(parseCount(value), value).toBeNull();
  });
});

describe("normalizeSocialLink", () => {
  it("adds https and accepts the platform's own domains", () => {
    expect(normalizeSocialLink("tiktok.com/@amara", "tiktok")).toBe("https://tiktok.com/@amara");
    expect(normalizeSocialLink("https://www.instagram.com/amara/", "instagram")).toBe("https://www.instagram.com/amara");
    expect(normalizeSocialLink("youtu.be/abc", "youtube")).toBe("https://youtu.be/abc");
    expect(normalizeSocialLink("http://m.youtube.com/@amara", "youtube")).toBe("https://m.youtube.com/@amara");
  });

  it("refuses links to another site", () => {
    expect(normalizeSocialLink("instagram.com/amara", "tiktok")).toBeNull();
    expect(normalizeSocialLink("eviltiktok.com/@amara", "tiktok")).toBeNull();
    expect(normalizeSocialLink("not a link", "linkedin")).toBeNull();
  });
});

describe("applicationSchema", () => {
  it("cleans up a good application", () => {
    expect(applicationSchema.parse(application)).toEqual({
      displayName: "Amara Okafor",
      xHandle: "AmaraBuilds",
      tiktok: undefined,
      youtube: "https://youtube.com/@amara",
      instagram: undefined,
      linkedin: "https://www.linkedin.com/in/amara",
      niches: ["ai", "startups"],
      followers: 18400,
      avgViews: 6200,
      country: "NG",
      bestPosts: ["https://x.com/amarabuilds/status/1", "https://x.com/amarabuilds/status/2", "https://twitter.com/amarabuilds/status/3"],
      why: "I review AI tools every week for founders who build in public.",
      referralCode: "9f3a1c2b",
    });
  });

  it("explains each problem on its own field", () => {
    const errors = errorsOf(
      applicationSchema.safeParse({
        ...application,
        displayName: "",
        xHandle: "@not valid",
        tiktok: "instagram.com/amara",
        niches: [],
        followers: "lots",
        country: "Narnia",
        bestPosts: ["x.com/a/status/1", "x.com/a/status/1", ""],
        why: "Pls",
        referralCode: "nope",
      }),
    );
    expect(errors).toMatchObject({
      displayName: "Tell us the name you post under.",
      xHandle: "Enter an X handle like @yourname.",
      tiktok: "Paste your profile link, like tiktok.com/@you.",
      niches: "Pick at least one.",
      followers: "A number, like 12,400 or 12.4k.",
      country: "Pick your country.",
      "bestPosts.2": "Paste a link to the post.",
      why: "A sentence or two, please.",
      referralCode: "Referral codes are 8 letters and numbers.",
    });
  });

  it("wants three different posts", () => {
    const errors = errorsOf(
      applicationSchema.safeParse({ ...application, bestPosts: ["x.com/a/status/1", "x.com/a/status/1", "x.com/a/status/2"] }),
    );
    expect(errors.bestPosts).toBe("Three different posts, please.");
  });

  it("doesn't call empty post links repeats", () => {
    const errors = errorsOf(applicationSchema.safeParse({ ...application, bestPosts: ["", "", ""] }));
    expect(errors.bestPosts).toBeUndefined();
    expect(errors["bestPosts.0"]).toBe("Paste a link to the post.");
  });

  it("takes up to five niches, all from the list", () => {
    expect(applicationSchema.safeParse({ ...application, niches: ["ai", "tech", "crypto", "startups", "design", "gaming"] }).success).toBe(false);
    expect(applicationSchema.safeParse({ ...application, niches: ["knitting"] }).success).toBe(false);
  });
});

describe("profileSchema", () => {
  const profile = {
    displayName: "Amara",
    tiktok: "",
    youtube: "",
    instagram: "",
    linkedin: "",
    niches: ["ai"],
    followers: "12000",
    avgViews: "3000",
    country: "GB",
    bio: "Builder.",
    ratePerPost: "",
    rateCurrency: "USDC" as const,
  };

  it("drops the currency when there's no rate", () => {
    expect(profileSchema.parse(profile)).toMatchObject({ ratePerPost: undefined, rateCurrency: undefined });
  });

  it("needs a currency with a rate, and a sensible price", () => {
    expect(errorsOf(profileSchema.safeParse({ ...profile, ratePerPost: "150", rateCurrency: undefined })).rateCurrency).toBe(
      "Pick a currency for your rate.",
    );
    expect(errorsOf(profileSchema.safeParse({ ...profile, ratePerPost: "$150" })).ratePerPost).toBe("A price like 150 or 150.50.");
    expect(profileSchema.parse({ ...profile, ratePerPost: "150.50" })).toMatchObject({ ratePerPost: "150.50", rateCurrency: "USDC" });
  });

  it("keeps the bio short", () => {
    expect(profileSchema.safeParse({ ...profile, bio: "x".repeat(301) }).success).toBe(false);
  });
});

describe("payoutSchema", () => {
  it("accepts a wallet in its network's format", () => {
    expect(payoutSchema.parse({ method: "crypto", asset: "USDC", network: "base", wallet: ` ${EVM} ` })).toEqual({
      method: "crypto",
      asset: "USDC",
      network: "base",
      wallet: EVM,
    });
    expect(payoutSchema.safeParse({ method: "crypto", asset: "USDC", network: "solana", wallet: SOLANA }).success).toBe(true);
    expect(payoutSchema.safeParse({ method: "crypto", asset: "USDT", network: "tron", wallet: TRON }).success).toBe(true);
  });

  it("catches an address from another network, and coins we don't send there", () => {
    expect(errorsOf(payoutSchema.safeParse({ method: "crypto", asset: "USDC", network: "base", wallet: SOLANA })).wallet).toMatch(
      /doesn't look like an address on this network/,
    );
    expect(errorsOf(payoutSchema.safeParse({ method: "crypto", asset: "USDT", network: "base", wallet: EVM })).network).toBe(
      "We don't send USDT on that network. Pick another.",
    );
    expect(errorsOf(payoutSchema.safeParse({ method: "crypto", asset: "USDC", network: "tron", wallet: TRON })).network).toBeDefined();
  });

  it("takes bank details and other arrangements", () => {
    expect(
      payoutSchema.parse({ method: "bank", bankCountry: "ng", bankName: "GTBank", accountName: "Amara Okafor", accountNumber: "0123456789" }),
    ).toMatchObject({ bankCountry: "NG", accountNumber: "0123456789" });
    expect(errorsOf(payoutSchema.safeParse({ method: "bank", bankCountry: "NG", bankName: "", accountName: "A", accountNumber: "12" }))).toMatchObject({
      bankName: "Which bank?",
      accountNumber: "Your account number or IBAN, letters and numbers only.",
    });
    expect(payoutSchema.safeParse({ method: "other", otherDetails: "Wise: amara@example.com" }).success).toBe(true);
    expect(payoutSchema.safeParse({ method: "cash" }).success).toBe(false);
  });

  it("agrees with the network list, which the database mirrors", () => {
    for (const network of CRYPTO_NETWORKS) {
      const sample = network.address === "evm" ? EVM : network.address === "solana" ? SOLANA : TRON;
      expect(isWalletAddress(network.value, sample), network.value).toBe(true);
    }
    expect(assetOnNetwork("USDT", "base")).toBe(false);
    expect(assetOnNetwork("USDC", "tron")).toBe(false);
  });
});

describe("inviteSchema", () => {
  it("takes an optional use limit and an expiry choice", () => {
    expect(inviteSchema.parse({ label: " Telegram ", maxUses: "", expiresIn: "never" })).toEqual({
      label: "Telegram",
      maxUses: undefined,
      expiresIn: "never",
    });
    expect(inviteSchema.parse({ label: "", maxUses: "25", expiresIn: "7d" })).toMatchObject({ maxUses: 25 });
    expect(inviteSchema.safeParse({ label: "", maxUses: "0", expiresIn: "never" }).success).toBe(false);
    expect(inviteSchema.safeParse({ label: "", maxUses: "2.5", expiresIn: "never" }).success).toBe(false);
    expect(inviteSchema.parse({ label: "", maxUses: "10,000", expiresIn: "never" }).maxUses).toBe(10_000);
    expect(inviteSchema.safeParse({ label: "", maxUses: "10,001", expiresIn: "never" }).success).toBe(false);
    expect(inviteSchema.safeParse({ label: "", maxUses: "", expiresIn: "forever" }).success).toBe(false);
  });
});

describe("lists", () => {
  it("has every country the forms need, by ISO code", () => {
    expect(COUNTRIES.length).toBeGreaterThan(240);
    expect(countryName("ng")).toBe("Nigeria");
    expect(countryName("GB")).toBe("United Kingdom");
    expect(isCountryCode("us")).toBe(true);
    expect(isCountryCode("EU")).toBe(false);
    for (const country of COUNTRIES) expect(country.code, country.name).toMatch(/^[A-Z]{2}$/);
    // Retired codes (YU, SU, UK...) would show a country twice.
    expect(new Set(COUNTRIES.map((country) => country.name)).size).toBe(COUNTRIES.length);
    expect(isCountryCode("YU")).toBe(false);
  });

  it("keeps niches in the order the forms show, with unique values", () => {
    expect(new Set(NICHES.map((niche) => niche.value)).size).toBe(NICHES.length);
  });
});
