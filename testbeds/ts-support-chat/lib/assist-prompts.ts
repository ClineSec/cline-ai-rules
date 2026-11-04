// Instructions for agent-assist drafts (app/api/assist/route.ts).

const TONE_GUIDES = {
  friendly: "Warm and plain-spoken; first names are fine.",
  neutral: "Matter-of-fact and brief.",
  formal: "Formal; no contractions, no exclamation marks.",
} as const;

export type Tone = keyof typeof TONE_GUIDES;

export function assistInstructions({ tone, agentName }: { tone: Tone; agentName: string }) {
  return `You draft replies for Example Cloud support agents. ${TONE_GUIDES[tone]}
Write in Markdown. Sign the reply as ${agentName}, Example Cloud Support.`;
}

export function toneGuide(tone: Tone) {
  return TONE_GUIDES[tone];
}
