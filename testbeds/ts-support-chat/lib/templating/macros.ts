import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import Handlebars from "handlebars";

/**
 * Reply macros: saved replies with {{placeholders}} that agents insert from the sidebar.
 * Agents can ask the assistant to suggest a macro from a solved ticket.
 */
const hb = Handlebars.create();
hb.registerHelper("firstName", (name: string) => name.split(" ")[0]);

export interface MacroFields {
  customer: { name: string; plan: string };
  agent: { name: string };
  ticket: { id: string; subject: string };
}

export interface SavedMacro {
  id: string;
  title: string;
  body: string;
  updatedBy: string;
}

const SAMPLE_FIELDS: MacroFields = {
  customer: { name: "Ada Example", plan: "Team" },
  agent: { name: "Sam" },
  ticket: { id: "T-1001", subject: "Example subject" },
};

const SUGGEST_INSTRUCTIONS = `Turn this solved ticket into a reusable reply macro. Use
{{firstName customer.name}}, {{agent.name}}, and {{ticket.id}} as placeholders.`;

/** Suggests a macro and checks that it compiles against sample fields before showing it. */
export async function suggestMacro(ticketText: string) {
  const { text } = await generateText({
    model: openai("gpt-4.1-mini"),
    system: SUGGEST_INSTRUCTIONS,
    prompt: ticketText,
  });
  const compiled = hb.compile(text, { strict: true });
  return { body: text, preview: compiled(SAMPLE_FIELDS) };
}

/** Saved macros are written and reviewed by support leads in the admin UI. */
export function renderSavedMacro(macro: SavedMacro, fields: MacroFields) {
  return hb.compile(macro.body, { strict: true })(fields);
}

const DRAFT_FRAME = hb.compile(
  "<p>Hi {{firstName customer.name}},</p>\n<div class=\"draft\">{{draft}}</div>\n<p>{{agent.name}}</p>",
);

/** A one-off drafted reply goes into the fixed frame as data. */
export async function frameDraft(ticketText: string, fields: MacroFields) {
  const { text } = await generateText({ model: openai("gpt-4.1-mini"), prompt: ticketText });
  return DRAFT_FRAME({ ...fields, draft: text });
}
