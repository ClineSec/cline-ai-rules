// Mermaid and KaTeX settings for diagrams and math in assistant answers.
import mermaid from "mermaid";
import katex from "katex";
import { z } from "zod";
import renderMathInElement from "katex/contrib/auto-render";

// --- Mermaid securityLevel -------------------------------------------------------------------

export function setupDiagrams() {
  mermaid.initialize({
    startOnLoad: false,
    theme: "neutral",
    // ruleid: mermaid-or-katex-unsafe-config
    securityLevel: "loose",
  });
}

const BASE_DIAGRAM_CONFIG = { startOnLoad: false, theme: "default" };

export function setupInteractiveDiagrams() {
  // ruleid: mermaid-or-katex-unsafe-config
  mermaid.mermaidAPI.initialize({ ...BASE_DIAGRAM_CONFIG, securityLevel: 'loose' });
}

const DIAGRAM_LEVEL = "loose";

export const diagramConfig = {
  // ruleid: mermaid-or-katex-unsafe-config
  securityLevel: DIAGRAM_LEVEL,
  flowchart: { htmlLabels: true },
};

enum SecurityLevel {
  Strict = "strict",
  Loose = "loose",
}

export function initFromEnum(interactive: boolean) {
  mermaid.initialize({
    // ruleid: mermaid-or-katex-unsafe-config
    securityLevel: interactive ? SecurityLevel.Loose : SecurityLevel.Strict,
  });
}

export const literalConfig = {
  // ruleid: mermaid-or-katex-unsafe-config
  securityLevel: "loose" as const,
  // ruleid: mermaid-or-katex-unsafe-config
  secure: ["startOnLoad"] as string[],
};

export function patchConfig(config: Record<string, unknown>) {
  // ruleid: mermaid-or-katex-unsafe-config
  config.securityLevel = "loose";
  return config;
}

export function strictDiagrams() {
  // ok: mermaid-or-katex-unsafe-config
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
}

export function sandboxedDiagrams() {
  // ok: mermaid-or-katex-unsafe-config
  mermaid.initialize({ startOnLoad: false, securityLevel: "sandbox" });
}

export function antiscriptDiagrams() {
  // ok: mermaid-or-katex-unsafe-config
  mermaid.initialize({ startOnLoad: false, securityLevel: "antiscript", htmlLabels: true });
}

// A level check is not a setting.
export function isLoose(config: { securityLevel?: string }) {
  // ok: mermaid-or-katex-unsafe-config
  return config.securityLevel === "loose";
}

// Types and schemas that list the levels are not settings.
// ok: mermaid-or-katex-unsafe-config
type LooseDiagramConfig = { securityLevel: "loose" | "strict" };

type DiagramPrefs = { securityLevel?: "strict" | "loose" | "antiscript" | "sandbox" };
const DEFAULT_DIAGRAM_PREFS: DiagramPrefs = { securityLevel: "strict" };

// A level read from saved preferences, with a value that starts with a parenthesized receiver.
// The enum check used to make OpenGrep 1.30.2 abort the whole file on these.
export function initFromPreferences(prefs: DiagramPrefs | undefined) {
  mermaid.initialize({
    // ok: mermaid-or-katex-unsafe-config
    securityLevel: (prefs ?? DEFAULT_DIAGRAM_PREFS).securityLevel,
  });
}

export function initWithLooseFallback(prefs: DiagramPrefs | undefined) {
  mermaid.initialize({
    // ruleid: mermaid-or-katex-unsafe-config
    securityLevel: (prefs ?? {}).securityLevel ?? "loose",
  });
}

export const diagramSettingsSchema = {
  // ok: mermaid-or-katex-unsafe-config
  securityLevel: z.enum(["strict", "loose", "antiscript", "sandbox"]).default("strict"),
};

export function levelFor(mode: string) {
  // ok: mermaid-or-katex-unsafe-config
  return { securityLevel: mode === "loose" ? "antiscript" : "strict" };
}

// --- Mermaid secure keys: init directives in the diagram text can't change securityLevel
// unless the site's `secure` list drops it.

export function setupWithOpenDirectives() {
  mermaid.initialize({
    securityLevel: "strict",
    // ruleid: mermaid-or-katex-unsafe-config
    secure: ["secure", "startOnLoad", "maxTextSize"],
  });
}

export function setupWithEmptySecureList() {
  // ruleid: mermaid-or-katex-unsafe-config
  mermaid.initialize({ securityLevel: "strict", secure: [] });
}

export function setupWithExtraSecureKey() {
  mermaid.initialize({
    securityLevel: "strict",
    // ok: mermaid-or-katex-unsafe-config
    secure: ["secure", "securityLevel", "startOnLoad", "maxTextSize", "themeCSS"],
  });
}

// --- KaTeX trust -----------------------------------------------------------------------------

export function renderFormula(tex: string, el: HTMLElement) {
  // ruleid: mermaid-or-katex-unsafe-config
  katex.render(tex, el, { throwOnError: false, trust: true });
}

export function formulaHtml(tex: string) {
  // ruleid: mermaid-or-katex-unsafe-config
  return katex.renderToString(tex, { displayMode: true, trust: () => true });
}

export function renderAllMath(root: HTMLElement) {
  renderMathInElement(root, {
    delimiters: [{ left: "$$", right: "$$", display: true }],
    // ruleid: mermaid-or-katex-unsafe-config
    trust: (context) => ["\\htmlId", "\\href"].includes(context.command),
  });
}

export const blocklistTrust = {
  // ruleid: mermaid-or-katex-unsafe-config
  trust: (context: { command: string }) => context.command !== "\\includegraphics",
};

const TRUSTED_COMMANDS = ["\\href", "\\htmlClass"];

export function renderTrustedList(tex: string) {
  return katex.renderToString(tex, {
    // ruleid: mermaid-or-katex-unsafe-config
    trust: (context) => TRUSTED_COMMANDS.includes(context.command),
  });
}

export function renderFunctionTrust(tex: string) {
  return katex.renderToString(tex, {
    // ruleid: mermaid-or-katex-unsafe-config
    trust: function () {
      return true;
    },
  });
}

export function renderDefault(tex: string) {
  // ok: mermaid-or-katex-unsafe-config
  return katex.renderToString(tex, { throwOnError: false, trust: false });
}

export function renderClassesOnly(tex: string) {
  // ok: mermaid-or-katex-unsafe-config
  return katex.renderToString(tex, { trust: (context) => context.command === "\\htmlClass" });
}

export function renderHttpsLinks(tex: string) {
  return katex.renderToString(tex, {
    // ok: mermaid-or-katex-unsafe-config
    trust: (context) => ["\\href", "\\url"].includes(context.command) && context.protocol === "https",
  });
}

export function renderAnchorsOnly(tex: string) {
  return katex.renderToString(tex, {
    // ok: mermaid-or-katex-unsafe-config
    trust: (context) => context.command === "\\href" && !!context.url?.startsWith("#eq-"),
  });
}

const SAFE_COMMANDS = new Set(["\\htmlClass", "\\htmlId"]);

export function renderSafeSet(tex: string) {
  return katex.renderToString(tex, {
    // ok: mermaid-or-katex-unsafe-config
    trust: (context) => SAFE_COMMANDS.has(context.command),
  });
}

export function renderRejectingAll(tex: string) {
  return katex.renderToString(tex, {
    // ok: mermaid-or-katex-unsafe-config
    trust: () => {
      throw new Error("HTML extensions are disabled");
    },
  });
}

export function renderEarlyReturn(tex: string) {
  return katex.renderToString(tex, {
    // ok: mermaid-or-katex-unsafe-config
    trust: (context) => {
      if (context.command !== "\\htmlId") return false;
      return true;
    },
  });
}

export const methodTrust = {
  output: "html" as const,
  // ruleid: mermaid-or-katex-unsafe-config
  trust(context: { command: string }) {
    return ["\\url", "\\htmlId"].includes(context.command);
  },
};

export const methodTrustChecked = {
  output: "html" as const,
  // ok: mermaid-or-katex-unsafe-config
  trust(context: { command: string; protocol?: string }) {
    return context.command === "\\href" && context.protocol === "https";
  },
};

export function renderListMethod(tex: string) {
  return katex.renderToString(tex, {
    // ruleid: mermaid-or-katex-unsafe-config
    trust: function (context) {
      return TRUSTED_COMMANDS.includes(context.command);
    },
  });
}

const LINK_COMMANDS = new Set(["\\url", "\\href"]);

export const linkTrust = {
  // ruleid: mermaid-or-katex-unsafe-config
  trust: (context: { command: string }) => LINK_COMMANDS.has(context.command),
};
