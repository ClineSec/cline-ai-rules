import { openai } from "@ai-sdk/openai";
import { ToolLoopAgent } from "ai";
import { HANDOFF_INSTRUCTIONS } from "./prompts";

export const handoffAgent = new ToolLoopAgent({
  model: openai("gpt-4.1"),
  instructions: HANDOFF_INSTRUCTIONS,
});
