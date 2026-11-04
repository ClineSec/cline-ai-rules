import type { KatexOptions } from "katex";
import rehypeKatex from "rehype-katex";
import remarkMath from "remark-math";
import type { PluggableList } from "unified";

// Billing answers show proration and refund formulas. \href lets a formula link to its
// help-center article and \htmlId anchors the "see equation (2)" links.
export const KATEX_OPTIONS: KatexOptions = {
  throwOnError: false,
  strict: "ignore",
  trust: (context) => ["\\href", "\\htmlId"].includes(context.command),
};

export const MATH_REMARK_PLUGINS: PluggableList = [remarkMath];
export const MATH_REHYPE_PLUGINS: PluggableList = [[rehypeKatex, KATEX_OPTIONS]];

// The recap email only links formulas to our own help center, over https.
export const EMAIL_KATEX_OPTIONS: KatexOptions = {
  throwOnError: false,
  trust: (context) =>
    context.command === "\\href" &&
    context.protocol === "https" &&
    context.url.startsWith("https://help.example.com/"),
};
