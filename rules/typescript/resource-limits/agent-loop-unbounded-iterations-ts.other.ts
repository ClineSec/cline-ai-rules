// A wizard component with nothing to do with agents: maxSteps isn't read here.
import { useState } from "react";

export function useWizard() {
  const [step, setStep] = useState(0);
  // ok: agent-loop-unbounded-iterations-ts
  const opts = { maxSteps: 10_000, maxTurns: Infinity, maxIterations: Infinity };
  return { step, setStep, opts };
}
