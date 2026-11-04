import {
  query,
  type HookCallback,
  type HookInput,
  type HookJSONOutput,
  type Options,
  type PreToolUseHookInput,
} from "@anthropic-ai/claude-agent-sdk";

const READ_ONLY_TOOLS = ["Read", "Glob", "Grep"];
const SHELL_MATCHER = "Bash";
const READ_ONLY_MATCHER = "Read|Glob|Grep";

const ALLOW: HookJSONOutput = {
  hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" },
};
const PASS: HookJSONOutput = {};

const approveConstant: HookCallback = async () => ALLOW;

async function approveConstantDecl(input: HookInput): Promise<HookJSONOutput> {
  if (input.hook_event_name !== "PreToolUse") return {};
  return ALLOW;
}

async function approveConstantForReads(input: HookInput): Promise<HookJSONOutput> {
  if ((input as PreToolUseHookInput).tool_name === "Read") return ALLOW;
  return PASS;
}

const passThrough: HookCallback = async () => PASS;

const approveEverything: HookCallback = async (input) => {
  console.log(`tool call ${(input as PreToolUseHookInput).tool_name}`);
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "unattended run",
    },
  };
};

const approveAfterEventGuard: HookCallback = async (input) => {
  if (input.hook_event_name !== "PreToolUse") return {};
  return { hookSpecificOutput: { hookEventName: input.hook_event_name, permissionDecision: "allow" } };
};

async function legacyApprove(_input: HookInput): Promise<HookJSONOutput> {
  return { decision: "approve", reason: "trusted job" };
}

const approveShellByName: HookCallback = async (input) => {
  const tool = (input as PreToolUseHookInput).tool_name;
  if (tool === "Read") return {};
  if (["Bash", "Write"].includes(tool)) {
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  }
  return {};
};

const approveReadOnly: HookCallback = async (input) => {
  if (READ_ONLY_TOOLS.includes((input as PreToolUseHookInput).tool_name)) {
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  }
  return {};
};

const approveReadsByName: HookCallback = async (input) => {
  const tool = (input as PreToolUseHookInput).tool_name;
  if (tool === "Grep") {
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  }
  return {};
};

async function gateShell(input: HookInput): Promise<HookJSONOutput> {
  const command = String(((input as PreToolUseHookInput).tool_input as { command?: string }).command ?? "");
  if (/^(git status|git diff|npm test)\b/.test(command)) {
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  }
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: "not on the allowlist",
    },
  };
}

const approveAfterPolicy: HookCallback = async (input) => {
  await policyEngine.enforce(input);
  return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
};

const approveByTernary: HookCallback = async (input) => ({
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: READ_ONLY_TOOLS.includes((input as PreToolUseHookInput).tool_name) ? "allow" : "ask",
  },
});

function preToolDecision(decision: "allow" | "ask", reason: string): HookJSONOutput {
  return {
    hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: decision, permissionDecisionReason: reason },
  };
}

const approveViaHelper: HookCallback = async () => preToolDecision("allow", "batch job");

async function gateViaHelper(input: HookInput): Promise<HookJSONOutput> {
  const path = String(((input as PreToolUseHookInput).tool_input as { file_path?: string }).file_path);
  if (path.startsWith("/srv/docs/")) {
    return preToolDecision("allow", "inside the docs tree");
  }
  return preToolDecision("ask", "outside the docs tree");
}

const auditLog: HookCallback = async (input) => {
  console.log(input.hook_event_name);
  return {};
};

export function unattendedOptions(): Options {
  return {
    hooks: {
      PreToolUse: [
        // ruleid: agent-sdk-hook-auto-approves-ts
        { hooks: [approveEverything] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { matcher: "*", hooks: [approveAfterEventGuard] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { matcher: SHELL_MATCHER, hooks: [legacyApprove], timeout: 30 },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { matcher: "mcp__.*", hooks: [approveEverything] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { matcher: "Read|WebFetch", hooks: [auditLog, approveEverything] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { hooks: [approveShellByName] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { matcher: "Bash", hooks: [approveConstant] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { hooks: [approveConstantDecl] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { matcher: "Bash", hooks: [approveViaHelper] },
        {
          matcher: "Write|Edit",
          hooks: [
            // ruleid: agent-sdk-hook-auto-approves-ts
            async () => ({ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } }),
          ],
        },
      ],
      PermissionRequest: [
        {
          hooks: [
            // ruleid: agent-sdk-hook-auto-approves-ts
            async () => ({
              hookSpecificOutput: { hookEventName: "PermissionRequest", decision: { behavior: "allow" } },
            }),
          ],
        },
      ],
    },
  };
}

export function gatedOptions(matcherFromConfig: string): Options {
  return {
    hooks: {
      PreToolUse: [
        // The documented read-only auto-approve: the matcher only reaches Read, Glob, Grep.
        // ok: agent-sdk-hook-auto-approves-ts
        { matcher: READ_ONLY_MATCHER, hooks: [approveEverything] },
        // ok: agent-sdk-hook-auto-approves-ts
        { matcher: "^(Read|Grep)$", hooks: [approveEverything] },
        // ok: agent-sdk-hook-auto-approves-ts
        { matcher: "mcp__tickets__get_ticket, Glob", hooks: [legacyApprove] },
        // The callback itself decides.
        // ok: agent-sdk-hook-auto-approves-ts
        { hooks: [approveReadOnly] },
        // ok: agent-sdk-hook-auto-approves-ts
        { hooks: [approveReadsByName] },
        // ok: agent-sdk-hook-auto-approves-ts
        { matcher: "Bash", hooks: [gateShell] },
        // ok: agent-sdk-hook-auto-approves-ts
        { hooks: [approveAfterPolicy] },
        // ok: agent-sdk-hook-auto-approves-ts
        { hooks: [approveByTernary] },
        // ok: agent-sdk-hook-auto-approves-ts
        { hooks: [auditLog] },
        // ok: agent-sdk-hook-auto-approves-ts
        { hooks: [approveConstantForReads, passThrough] },
        // ok: agent-sdk-hook-auto-approves-ts
        { matcher: "Write|Edit", hooks: [gateViaHelper] },
        // A matcher read from configuration can't be judged here.
        // ok: agent-sdk-hook-auto-approves-ts
        { matcher: matcherFromConfig, hooks: [approveEverything] },
      ],
    },
  };
}

export function bypassOptions(): Options {
  // Reported by agent-sdk-bypass-permissions-ts.
  return {
    permissionMode: "bypassPermissions",
    allowDangerouslySkipPermissions: true,
    // ok: agent-sdk-hook-auto-approves-ts
    hooks: { PreToolUse: [{ hooks: [approveEverything] }] },
  };
}

export async function run(prompt: string) {
  for await (const message of query({ prompt, options: unattendedOptions() })) {
    console.log(message.type);
  }
}

// Callbacks registered through a list, a function expression, a class, or a factory.
const approveExpr = async function (input: HookInput): Promise<HookJSONOutput> {
  console.log(`tool call ${(input as PreToolUseHookInput).tool_name}`);
  return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
};

const approveNamedExpr: HookCallback = async function approveNamed(_input) {
  return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
};

const approveExprConstant: HookCallback = async function (_input) {
  return ALLOW;
};

function makeApprover(reason: string): HookCallback {
  return async () => ({
    hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: reason },
  });
}

const makeCurriedApprover = (reason: string) => async (_input: HookInput) => ({
  hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: reason },
});

function makeReadsApprover(): HookCallback {
  return async (input) => {
    if (READ_ONLY_TOOLS.includes((input as PreToolUseHookInput).tool_name)) {
      return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
    }
    return {};
  };
}

const approvers: HookCallback[] = [approveEverything];
const checked = [approveReadOnly];

class BatchRunner {
  private approveField: HookCallback = async () => ({
    hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" },
  });

  private readonly fieldConstant = async () => ALLOW;

  async approveMethod(_input: HookInput): Promise<HookJSONOutput> {
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  }

  async approveMethodConstant(_input: HookInput): Promise<HookJSONOutput> {
    return ALLOW;
  }

  async gateMethod(input: HookInput): Promise<HookJSONOutput> {
    if (READ_ONLY_TOOLS.includes((input as PreToolUseHookInput).tool_name)) {
      return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
    }
    return {};
  }

  options(): Options {
    const hooks = {
      PreToolUse: [
        // ruleid: agent-sdk-hook-auto-approves-ts
        { matcher: "Bash", hooks: [this.approveMethod.bind(this)] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { hooks: [this.approveMethod] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { matcher: "Write|Edit", hooks: [this.approveField] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { hooks: [this.approveMethodConstant] },
        // ruleid: agent-sdk-hook-auto-approves-ts
        { matcher: "Bash", hooks: [this.fieldConstant] },
        // ok: agent-sdk-hook-auto-approves-ts
        { hooks: [this.gateMethod.bind(this)] },
        // ok: agent-sdk-hook-auto-approves-ts
        { matcher: "Read", hooks: [this.approveMethod] },
      ],
    };
    return { hooks };
  }
}

export const batchOptions: Options = {
  hooks: {
    PreToolUse: [
      // ruleid: agent-sdk-hook-auto-approves-ts
      { matcher: "Bash", hooks: [approveExpr] },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { hooks: [approveNamedExpr] },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { matcher: "mcp__.*", hooks: [approveExprConstant] },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { matcher: "Bash", hooks: [makeApprover("nightly")] },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { hooks: [makeCurriedApprover("nightly")] },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { matcher: "Bash|Write", hooks: approvers },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { hooks: approvers },
      // ok: agent-sdk-hook-auto-approves-ts
      { matcher: READ_ONLY_MATCHER, hooks: approvers },
      // ok: agent-sdk-hook-auto-approves-ts
      { hooks: checked },
      // ok: agent-sdk-hook-auto-approves-ts
      { hooks: [makeReadsApprover()] },
      // ok: agent-sdk-hook-auto-approves-ts
      { matcher: "Glob", hooks: [makeApprover("reads")] },
    ],
  },
};

// A matcher kept in a const and listed later.
// ruleid: agent-sdk-hook-auto-approves-ts
const shellHook = { matcher: "Bash", hooks: [approveEverything] };
export const shellOptions: Options = { hooks: { PreToolUse: [shellHook] } };

function makeConstantApprover(): HookCallback {
  return async () => ALLOW;
}

export const constantFactoryOptions: Options = {
  // ruleid: agent-sdk-hook-auto-approves-ts
  hooks: { PreToolUse: [{ matcher: "Write", hooks: [makeConstantApprover()] }] },
};

// Factories that hand back a function rather than an arrow, and a block-bodied arrow factory.
function makeNamedApprover(reason: string): HookCallback {
  return async function allowAll(_input) {
    return {
      hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: reason },
    };
  };
}

function makeAnonymousApprover() {
  return async function (_input: HookInput): Promise<HookJSONOutput> {
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  };
}

function makeInnerApprover(job: string): HookCallback {
  async function inner(input: HookInput): Promise<HookJSONOutput> {
    console.log(`${job}: ${(input as PreToolUseHookInput).tool_name}`);
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  }
  return inner;
}

function makeInnerConstantApprover(): HookCallback {
  async function inner(_input: HookInput): Promise<HookJSONOutput> {
    return ALLOW;
  }
  return inner;
}

const makeBlockApprover = (reason: string) => {
  const label = `[${reason}]`;
  return async (_input: HookInput) => ({
    hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: label },
  });
};

function makeInnerReadsApprover(): HookCallback {
  async function inner(input: HookInput): Promise<HookJSONOutput> {
    if (READ_ONLY_TOOLS.includes((input as PreToolUseHookInput).tool_name)) {
      return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
    }
    return {};
  }
  return inner;
}

// Declares an approve-all helper but returns the audit callback, which decides nothing.
function makeAuditHook(): HookCallback {
  async function allowAll(_input: HookInput): Promise<HookJSONOutput> {
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  }
  async function audit(input: HookInput): Promise<HookJSONOutput> {
    console.log((input as PreToolUseHookInput).tool_name);
    return {};
  }
  void allowAll;
  return audit;
}

const factoryFunctionHooks = [makeInnerApprover("sweep")];

export const factoryFunctionOptions: Options = {
  hooks: {
    PreToolUse: [
      // ruleid: agent-sdk-hook-auto-approves-ts
      { matcher: "Bash", hooks: [makeNamedApprover("nightly")] },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { hooks: [makeAnonymousApprover()] },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { matcher: "Write|Edit", hooks: [makeInnerApprover("sweep")] },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { matcher: "Bash", hooks: [makeInnerConstantApprover()] },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { hooks: [makeBlockApprover("nightly")] },
      // ruleid: agent-sdk-hook-auto-approves-ts
      { matcher: "Bash", hooks: factoryFunctionHooks },
      // ok: agent-sdk-hook-auto-approves-ts
      { hooks: [makeInnerReadsApprover()] },
      // ok: agent-sdk-hook-auto-approves-ts
      { hooks: [makeAuditHook()] },
      // ok: agent-sdk-hook-auto-approves-ts
      { matcher: "Read", hooks: [makeNamedApprover("reads")] },
    ],
  },
};
