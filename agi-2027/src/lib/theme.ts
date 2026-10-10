export type Theme = "dark" | "light";

export const THEME_STORAGE_KEY = "agi-theme";
export const DEFAULT_THEME: Theme = "light";

/** Browser chrome color (address bar on phones) for each theme. */
export const THEME_COLOR: Record<Theme, string> = {
  dark: "#121110",
  light: "#eeece8",
};

/**
 * Runs in <head> before first paint. Applies the saved theme so a light-mode
 * dark-mode visitor never sees a light flash (and the other way round).
 */
export const themeScript = `(function(){try{var t=localStorage.getItem("${THEME_STORAGE_KEY}");if(t!=="light"&&t!=="dark")t="${DEFAULT_THEME}";var d=document.documentElement;d.setAttribute("data-theme",t);var m=document.querySelector('meta[name="theme-color"]');if(m)m.setAttribute("content",t==="light"?"${THEME_COLOR.light}":"${THEME_COLOR.dark}")}catch(e){}})()`;

export function readStoredTheme(): Theme {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY);
    return value === "light" || value === "dark" ? value : DEFAULT_THEME;
  } catch {
    return DEFAULT_THEME;
  }
}

export function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.setAttribute("data-theme", theme);
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", THEME_COLOR[theme]);
}

export function storeTheme(theme: Theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Private mode or storage disabled: the choice lasts for this page only.
  }
}
