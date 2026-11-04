/** Endpoints and credentials for the services the agents publish to and report from. */
export const integrations = {
  npm: {
    registry: "https://registry.ci-fixer.invalid/",
    publishToken: process.env.NPM_PUBLISH_TOKEN ?? "",
  },
  sentry: {
    apiBase: "https://sentry.ci-fixer.invalid/api/0",
    org: "example-org",
    authToken: process.env.SENTRY_AUTH_TOKEN ?? "",
  },
  statusUrl: "https://status.example.com",
};
