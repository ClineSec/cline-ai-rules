// Prints Bedrock credentials for Claude Code's awsCredentialExport setting.
// The platform team's broker writes a short-lived grant to this file; we only reshape it.
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const grantPath = join(homedir(), ".config", "ci-fixer", "bedrock-grant.json");
const grant = JSON.parse(readFileSync(grantPath, "utf8"));

process.stdout.write(
  JSON.stringify({
    Credentials: {
      AccessKeyId: grant.accessKeyId,
      SecretAccessKey: grant.secretAccessKey,
      SessionToken: grant.sessionToken,
    },
  }),
);
