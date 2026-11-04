import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { env } from "./engine";

export interface Incident {
  id: string;
  title: string;
  startedAt: string;
  components: string[];
  notes: string;
}

const BANNER_INSTRUCTIONS = `Write a two-sentence customer-facing status update for this
incident. Plain language, no blame, no internal hostnames.`;

// The banner wraps the update in our own markup, then fills in the incident fields.
const BANNER_OPEN = `<div class="banner banner--{{ severity }}"><strong>{{ title }}</strong> `;
const BANNER_CLOSE = ` <span class="since">Started {{ startedAt | since }}</span></div>`;

/** The banner shown on every help-center page while an incident is open. */
export async function renderIncidentBanner(incident: Incident, severity: "minor" | "major") {
  const update = await generateText({
    model: openai("gpt-4.1-mini"),
    system: BANNER_INSTRUCTIONS,
    prompt: `${incident.title}\nAffected: ${incident.components.join(", ")}\n\n${incident.notes}`,
  });

  return env.renderString(BANNER_OPEN + update.text + BANNER_CLOSE, {
    severity,
    title: incident.title,
    startedAt: incident.startedAt,
  });
}

/** The full status page keeps the update as data in a template file. */
export async function renderStatusPage(incident: Incident) {
  const update = await generateText({
    model: openai("gpt-4.1-mini"),
    system: BANNER_INSTRUCTIONS,
    prompt: `${incident.title}\n\n${incident.notes}`,
  });

  return env.render("incident.njk", { incident, update: update.text });
}
