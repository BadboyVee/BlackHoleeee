export type Theme = "dark" | "light";

/**
 * A look is a complete visual direction for the site: palette, type, hero and
 * motion. Light and dark mode work inside every look.
 */
export type Look = "renaissance" | "agent" | "drop";

export const THEME_STORAGE_KEY = "agi-theme";
export const LOOK_STORAGE_KEY = "agi-look";
export const DEFAULT_THEME: Theme = "light";
/** The owner's pick (17 Oct 2026): what visitors, shared links and sign in show first. */
export const DEFAULT_LOOK: Look = "renaissance";

export const LOOKS: { id: Look; name: string; description: string }[] = [
  {
    id: "renaissance",
    name: "Renaissance",
    description: "A living old-master painting with bold white type and a hot pink signal.",
  },
  {
    id: "agent",
    name: "Agent",
    description: "Warm red, a felt 3D host who watches your cursor, and a chat-style hello.",
  },
  {
    id: "drop",
    name: "Drop",
    description: "Giant words behind the product, juicy color blocks and floating icons.",
  },
];

export function isLook(value: unknown): value is Look {
  return value === "renaissance" || value === "agent" || value === "drop";
}

/** Browser chrome color (address bar on phones) for each look and mode. */
export const THEME_COLOR: Record<Look, Record<Theme, string>> = {
  renaissance: { light: "#ece5d5", dark: "#10150e" },
  agent: { light: "#f4f0ec", dark: "#150b0a" },
  drop: { light: "#fbf8f4", dark: "#110f0e" },
};

/** The hero image each look paints first, preloaded before the page renders. */
export const LOOK_PRELOAD: Partial<Record<Look, { href: string; srcset: string; sizes: string }>> = {
  renaissance: {
    href: "/art/orion-1600.webp",
    srcset: "/art/orion-1600.webp 1600w, /art/orion-2400.webp 2400w",
    sizes: "(max-aspect-ratio: 1535/1000) 154vh, 100vw",
  },
};

/**
 * Runs in <head> before first paint. Applies the saved mode and look so nobody
 * sees a flash of the wrong one. `?look=agent` in the URL picks a look and
 * remembers it, which makes each look easy to share.
 */
export const themeScript = `(function(){try{var d=document.documentElement,s=localStorage,t=s.getItem("${THEME_STORAGE_KEY}");if(t!=="light"&&t!=="dark")t="${DEFAULT_THEME}";var L=["renaissance","agent","drop"],q=new URLSearchParams(location.search).get("look"),l=s.getItem("${LOOK_STORAGE_KEY}");if(L.indexOf(q)>-1){l=q;s.setItem("${LOOK_STORAGE_KEY}",q)}if(L.indexOf(l)<0)l="${DEFAULT_LOOK}";d.setAttribute("data-theme",t);d.setAttribute("data-look",l);var C=${JSON.stringify(
  THEME_COLOR,
)},m=document.querySelector('meta[name="theme-color"]');if(m)m.setAttribute("content",C[l][t]);var P=${JSON.stringify(
  LOOK_PRELOAD,
)};var p=P[l];if(p&&location.pathname==="/"){var k=document.createElement("link");k.rel="preload";k.as="image";k.href=p.href;k.setAttribute("imagesrcset",p.srcset);k.setAttribute("imagesizes",p.sizes);k.setAttribute("fetchpriority","high");document.head.appendChild(k)}}catch(e){}})()`;

export function readStoredTheme(): Theme {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY);
    return value === "light" || value === "dark" ? value : DEFAULT_THEME;
  } catch {
    return DEFAULT_THEME;
  }
}

export function readStoredLook(): Look {
  try {
    const value = localStorage.getItem(LOOK_STORAGE_KEY);
    return isLook(value) ? value : DEFAULT_LOOK;
  } catch {
    return DEFAULT_LOOK;
  }
}

/** The look currently on the page (the inline script sets it before paint). */
export function currentLook(): Look {
  const value = document.documentElement.getAttribute("data-look");
  return isLook(value) ? value : DEFAULT_LOOK;
}

export function currentTheme(): Theme {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

function syncThemeColor() {
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", THEME_COLOR[currentLook()][currentTheme()]);
}

export function applyTheme(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
  syncThemeColor();
}

export function applyLook(look: Look) {
  document.documentElement.setAttribute("data-look", look);
  syncThemeColor();
  window.dispatchEvent(new CustomEvent("agi:look", { detail: look }));
}

export function storeTheme(theme: Theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Private mode or storage disabled: the choice lasts for this page only.
  }
}

export function storeLook(look: Look) {
  try {
    localStorage.setItem(LOOK_STORAGE_KEY, look);
  } catch {
    // Same as above.
  }
}

/** Subscribe to look changes from this tab and others (for useSyncExternalStore). */
export function subscribeLook(onChange: () => void) {
  function onStorage(event: StorageEvent) {
    if (event.key === LOOK_STORAGE_KEY) {
      applyLook(readStoredLook());
    }
  }
  window.addEventListener("agi:look", onChange);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener("agi:look", onChange);
    window.removeEventListener("storage", onStorage);
  };
}
