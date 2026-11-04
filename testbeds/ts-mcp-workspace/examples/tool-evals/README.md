# Tool evals

Scripted sessions that drive opencode or Kilo Code against the workspace tools and score
whether the model picked the right tool. Start the agent from this folder so it picks up the
config here on top of the repository's `opencode.jsonc`.

Eval runs go through the shared eval gateway so every run's transcript lands in the eval
dashboard; the local Ollama provider is for offline smoke runs. Kilo's codebase index for this
folder lives in the team's hosted Qdrant so the eval prompts can cite tool sources.
