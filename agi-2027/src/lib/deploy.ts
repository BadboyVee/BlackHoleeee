/*
 * Which deployment is running: the live site, a preview link, or a laptop.
 * Vercel says so in VERCEL_ENV and Netlify in CONTEXT, but Netlify hands the
 * running site fewer variables than the build. So next.config.ts works it out
 * once, while building, and bakes the answer into the code as
 * AGI_DEPLOY_STAGE, AGI_DEPLOY_URL and AGI_DEPLOY_HOST. The site reads only
 * those.
 */

type Env = Record<string, string | undefined>;

export type DeployStage = "production" | "preview" | "development";

/** Which host built the site: "" for local development or anywhere else. */
export type DeployHost = "vercel" | "netlify" | "";

/** Vercel sets VERCEL=1 and Netlify sets NETLIFY=true in the build. */
export function deployHostFrom(env: Env): DeployHost {
  if (env.VERCEL === "1") return "vercel";
  if (env.NETLIFY === "true") return "netlify";
  return "";
}

/** The stage from the host's build variables, on Vercel or Netlify. */
export function deployStageFrom(env: Env): DeployStage {
  if (env.VERCEL_ENV === "production" || env.CONTEXT === "production") return "production";
  if (env.VERCEL_ENV === "preview" || env.CONTEXT === "deploy-preview" || env.CONTEXT === "branch-deploy") {
    return "preview";
  }
  return "development";
}

/** The address the host gives this deployment, or "" when it gives none. */
export function deployUrlFrom(env: Env): string {
  const live = deployStageFrom(env) === "production";
  if (env.VERCEL_ENV) {
    const host = live ? env.VERCEL_PROJECT_PRODUCTION_URL : env.VERCEL_URL;
    return host ? `https://${host}` : "";
  }
  if (env.CONTEXT) return (live ? env.URL : env.DEPLOY_PRIME_URL) || "";
  return "";
}

/** True on the live site; false on preview links and in local development. */
export function isLiveSite(): boolean {
  return process.env.AGI_DEPLOY_STAGE === "production";
}
