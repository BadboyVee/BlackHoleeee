/*
 * Choices on the creator application, profile and payout forms. The database
 * checks the same lists (private.known_niches and the payout_details checks
 * in supabase/migrations/20261013140000_creator_onboarding.sql).
 */

export const NICHES = [
  { value: "ai", label: "AI" },
  { value: "tech", label: "Tech" },
  { value: "crypto", label: "Crypto" },
  { value: "startups", label: "Startups" },
  { value: "design", label: "Design" },
  { value: "dev_tools", label: "Dev tools" },
  { value: "productivity", label: "Productivity" },
  { value: "finance", label: "Finance" },
  { value: "gaming", label: "Gaming" },
  { value: "science", label: "Science" },
  { value: "marketing", label: "Marketing" },
  { value: "other", label: "Something else" },
] as const;

export type Niche = (typeof NICHES)[number]["value"];
export const NICHE_VALUES = NICHES.map((niche) => niche.value) as [Niche, ...Niche[]];
export const MAX_NICHES = 5;

export function nicheLabel(value: string): string {
  return NICHES.find((niche) => niche.value === value)?.label ?? value;
}

export const PAYOUT_METHODS = [
  { value: "crypto", label: "Crypto", hint: "USDC or USDT to your wallet." },
  { value: "bank", label: "Bank transfer", hint: "To an account in your name." },
  { value: "other", label: "Something else", hint: "Tell us how, and we'll check it works." },
] as const;

export type PayoutMethod = (typeof PAYOUT_METHODS)[number]["value"];

export const CRYPTO_ASSETS = ["USDC", "USDT"] as const;
export type CryptoAsset = (typeof CRYPTO_ASSETS)[number];

/** Each network, the address format it uses, and which stablecoins we send on it. */
export const CRYPTO_NETWORKS = [
  { value: "base", label: "Base", address: "evm", assets: ["USDC"] },
  { value: "solana", label: "Solana", address: "solana", assets: ["USDC", "USDT"] },
  { value: "ethereum", label: "Ethereum", address: "evm", assets: ["USDC", "USDT"] },
  { value: "polygon", label: "Polygon", address: "evm", assets: ["USDC", "USDT"] },
  { value: "arbitrum", label: "Arbitrum", address: "evm", assets: ["USDC", "USDT"] },
  { value: "tron", label: "Tron", address: "tron", assets: ["USDT"] },
] as const satisfies readonly { value: string; label: string; address: string; assets: readonly CryptoAsset[] }[];

export type CryptoNetwork = (typeof CRYPTO_NETWORKS)[number]["value"];
export const NETWORK_VALUES = CRYPTO_NETWORKS.map((network) => network.value) as [CryptoNetwork, ...CryptoNetwork[]];

const ADDRESS_FORMATS = {
  evm: { pattern: /^0x[0-9a-fA-F]{40}$/, example: "0x followed by 40 letters and numbers" },
  solana: { pattern: /^[1-9A-HJ-NP-Za-km-z]{32,44}$/, example: "32 to 44 letters and numbers" },
  tron: { pattern: /^T[1-9A-HJ-NP-Za-km-z]{33}$/, example: "a T followed by 33 letters and numbers" },
} as const;

export function networkMeta(value: string) {
  return CRYPTO_NETWORKS.find((network) => network.value === value);
}

export function networkLabel(value: string): string {
  return networkMeta(value)?.label ?? value;
}

/** True when the address is in the network's format. The database checks the same patterns. */
export function isWalletAddress(network: string, address: string): boolean {
  const meta = networkMeta(network);
  return Boolean(meta && ADDRESS_FORMATS[meta.address].pattern.test(address));
}

export function addressExample(network: string): string {
  const meta = networkMeta(network);
  return meta ? ADDRESS_FORMATS[meta.address].example : "";
}

/** True when we send that stablecoin on that network (no USDT on Base, no USDC on Tron). */
export function assetOnNetwork(asset: string, network: string): boolean {
  const meta = networkMeta(network);
  return Boolean(meta && (meta.assets as readonly string[]).includes(asset));
}

/** "…9EE7": the end of an address or account number, for confirmations. */
export function lastFour(value: string): string {
  return value.trim().slice(-4);
}
