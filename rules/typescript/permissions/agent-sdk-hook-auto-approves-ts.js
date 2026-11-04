import { query } from "@anthropic-ai/claude-agent-sdk";

const approveAll = async () => ({
  hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" },
});

async function approveReadOnly(input) {
  if (["Read", "Glob", "Grep"].includes(input.tool_name)) {
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  }
  return {};
}

export async function runJob(prompt) {
  const options = {
    hooks: {
      PreToolUse: [
        // ruleid: agent-sdk-hook-auto-approves-ts
        { matcher: "Bash|Write|Edit", hooks: [approveAll] },
        // ok: agent-sdk-hook-auto-approves-ts
        { hooks: [approveReadOnly] },
        // ok: agent-sdk-hook-auto-approves-ts
        { matcher: "Glob", hooks: [approveAll] },
      ],
    },
  };
  for await (const message of query({ prompt, options })) {
    console.log(message.type);
  }
}

const approveExpr = function (_input) {
  return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
};

class Runner {
  async approveMethod() {
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  }

  options() {
    return {
      hooks: {
        PreToolUse: [
          // ruleid: agent-sdk-hook-auto-approves-ts
          { matcher: "Bash", hooks: [this.approveMethod.bind(this)] },
          // ruleid: agent-sdk-hook-auto-approves-ts
          { matcher: "Edit", hooks: [approveExpr] },
          // ok: agent-sdk-hook-auto-approves-ts
          { matcher: "Grep", hooks: [approveExpr] },
        ],
      },
    };
  }
}

export { Runner };

function makeApprover() {
  return async function (_input) {
    return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow" } };
  };
}

export const factoryOptions = {
  hooks: {
    PreToolUse: [
      // ruleid: agent-sdk-hook-auto-approves-ts
      { matcher: "Bash", hooks: [makeApprover()] },
      // ok: agent-sdk-hook-auto-approves-ts
      { matcher: "Grep", hooks: [makeApprover()] },
    ],
  },
};
