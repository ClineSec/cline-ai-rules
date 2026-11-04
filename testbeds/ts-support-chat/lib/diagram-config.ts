import type { MermaidConfig } from "mermaid";

/**
 * Mermaid settings for flowcharts in assistant answers ("how do I reset my router" comes back
 * as a decision tree). Support leads wanted each step to open its help-center article, and
 * click links only work in loose mode.
 */
export const DIAGRAM_CONFIG: MermaidConfig = {
  startOnLoad: false,
  theme: "neutral",
  securityLevel: "loose",
  flowchart: { htmlLabels: true, curve: "basis" },
};

/** Diagrams attached to tickets as SVG are static: no links, no click handlers. */
export const EXPORT_DIAGRAM_CONFIG: MermaidConfig = {
  ...DIAGRAM_CONFIG,
  securityLevel: "strict",
};

export const DIAGRAM_LANGUAGES = new Set(["mermaid", "flowchart"]);

export function isDiagramFence(language: string | undefined): boolean {
  return language !== undefined && DIAGRAM_LANGUAGES.has(language.toLowerCase());
}
