import { afterEach, describe, expect, it, vi } from "vitest";

import { deployHostFrom, deployStageFrom, deployUrlFrom, isLiveSite } from "@/lib/deploy";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("deployHostFrom", () => {
  it("knows Vercel and Netlify by the flags they set in the build", () => {
    expect(deployHostFrom({ VERCEL: "1" })).toBe("vercel");
    expect(deployHostFrom({ NETLIFY: "true" })).toBe("netlify");
  });

  it("is empty anywhere else", () => {
    expect(deployHostFrom({})).toBe("");
    expect(deployHostFrom({ VERCEL: "0", NETLIFY: "false" })).toBe("");
  });
});

describe("deployStageFrom", () => {
  it("reads Vercel's VERCEL_ENV", () => {
    expect(deployStageFrom({ VERCEL_ENV: "production" })).toBe("production");
    expect(deployStageFrom({ VERCEL_ENV: "preview" })).toBe("preview");
    expect(deployStageFrom({ VERCEL_ENV: "development" })).toBe("development");
  });

  it("reads Netlify's CONTEXT", () => {
    expect(deployStageFrom({ CONTEXT: "production" })).toBe("production");
    expect(deployStageFrom({ CONTEXT: "deploy-preview" })).toBe("preview");
    expect(deployStageFrom({ CONTEXT: "branch-deploy" })).toBe("preview");
    expect(deployStageFrom({ CONTEXT: "dev" })).toBe("development");
  });

  it("is development anywhere else", () => {
    expect(deployStageFrom({})).toBe("development");
    expect(deployStageFrom({ NODE_ENV: "production" })).toBe("development");
  });
});

describe("deployUrlFrom", () => {
  it("uses Vercel's production domain on the live site and the deployment's own URL on previews", () => {
    const vercel = { VERCEL_PROJECT_PRODUCTION_URL: "agi2027.com", VERCEL_URL: "agi-2027-abc123.vercel.app" };
    expect(deployUrlFrom({ ...vercel, VERCEL_ENV: "production" })).toBe("https://agi2027.com");
    expect(deployUrlFrom({ ...vercel, VERCEL_ENV: "preview" })).toBe("https://agi-2027-abc123.vercel.app");
  });

  it("uses Netlify's main URL on the live site and the deploy's prime URL on previews", () => {
    const netlify = { URL: "https://agi2027.netlify.app", DEPLOY_PRIME_URL: "https://deploy-preview-5--agi2027.netlify.app" };
    expect(deployUrlFrom({ ...netlify, CONTEXT: "production" })).toBe("https://agi2027.netlify.app");
    expect(deployUrlFrom({ ...netlify, CONTEXT: "deploy-preview" })).toBe("https://deploy-preview-5--agi2027.netlify.app");
    expect(deployUrlFrom({ ...netlify, CONTEXT: "branch-deploy" })).toBe("https://deploy-preview-5--agi2027.netlify.app");
  });

  it("is empty when the host gives no address", () => {
    expect(deployUrlFrom({})).toBe("");
    expect(deployUrlFrom({ VERCEL_ENV: "production" })).toBe("");
    expect(deployUrlFrom({ CONTEXT: "production" })).toBe("");
  });
});

describe("isLiveSite", () => {
  it("is true only for the production stage baked in at build", () => {
    vi.stubEnv("AGI_DEPLOY_STAGE", "production");
    expect(isLiveSite()).toBe(true);
    for (const stage of ["preview", "development", ""]) {
      vi.stubEnv("AGI_DEPLOY_STAGE", stage);
      expect(isLiveSite(), stage).toBe(false);
    }
  });
});
