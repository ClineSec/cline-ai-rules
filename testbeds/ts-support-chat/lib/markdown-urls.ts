import { defaultUrlTransform } from "react-markdown";

/** Hosts whose images and links may appear in rendered answers. */
export const HELP_CENTER_HOSTS = new Set(["help.example.com", "docs.example.com"]);

/**
 * react-markdown urlTransform for model-written text: links keep react-markdown's protocol
 * check, and images load only from the help center (anything else would be fetched by the
 * agent's browser as soon as the reply renders).
 */
export function helpCenterUrlsOnly(url: string, key: string): string {
  const safe = defaultUrlTransform(url);
  if (key !== "src" || !safe) return safe;
  try {
    return HELP_CENTER_HOSTS.has(new URL(safe).hostname) ? safe : "";
  } catch {
    return "";
  }
}
