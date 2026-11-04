import path from "node:path";
import nunjucks from "nunjucks";

/** Nunjucks environment for the status page and its banners (templates/status/*.njk). */
export const env = nunjucks.configure(path.join(process.cwd(), "templates", "status"), {
  autoescape: true,
  throwOnUndefined: true,
});

env.addFilter("since", (iso: string) => {
  const minutes = Math.round((Date.now() - Date.parse(iso)) / 60_000);
  return minutes < 60 ? `${minutes} min ago` : `${Math.round(minutes / 60)} h ago`;
});
