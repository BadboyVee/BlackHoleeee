import { describe, expect, it } from "vitest";

import { clientIp } from "@/lib/request-ip";

describe("clientIp", () => {
  it("on Netlify, reads only x-nf-client-connection-ip", () => {
    const spoofed = new Headers({
      "x-forwarded-for": "6.6.6.6",
      "x-real-ip": "7.7.7.7",
      "x-nf-client-connection-ip": " 192.0.2.10 ",
    });
    expect(clientIp(spoofed, "netlify")).toBe("192.0.2.10");
    expect(clientIp(new Headers({ "x-forwarded-for": "6.6.6.6" }), "netlify")).toBe("unknown");
  });

  it("on Vercel, reads the first x-forwarded-for entry, which Vercel sets", () => {
    const list = new Headers({ "x-forwarded-for": "203.0.113.7, 10.0.0.1", "x-nf-client-connection-ip": "6.6.6.6" });
    expect(clientIp(list, "vercel")).toBe("203.0.113.7");
  });

  it("falls back to x-real-ip, then to 'unknown'", () => {
    expect(clientIp(new Headers({ "x-real-ip": "198.51.100.4" }), "vercel")).toBe("198.51.100.4");
    expect(clientIp(new Headers(), "vercel")).toBe("unknown");
    expect(clientIp(new Headers({ "x-forwarded-for": " , 10.0.0.1" }), "")).toBe("unknown");
  });
});
