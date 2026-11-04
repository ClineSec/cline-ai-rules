"use client";

import { useEffect, useId, useRef, useState } from "react";
import mermaid from "mermaid";
import { DIAGRAM_CONFIG, EXPORT_DIAGRAM_CONFIG } from "@/lib/diagram-config";

let configured: "chat" | "export" | null = null;

function configureMermaid(mode: "chat" | "export") {
  if (configured !== mode) {
    mermaid.initialize(mode === "chat" ? DIAGRAM_CONFIG : EXPORT_DIAGRAM_CONFIG);
    configured = mode;
  }
}

/** A ```mermaid fence from an assistant answer, drawn in place. */
export function DiagramBlock({ source, mode = "chat" }: { source: string; mode?: "chat" | "export" }) {
  const ref = useRef<HTMLDivElement>(null);
  const id = `diagram-${useId().replace(/:/g, "")}`;
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    configureMermaid(mode);
    let cancelled = false;
    mermaid
      .render(id, source)
      .then(({ svg, bindFunctions }) => {
        if (cancelled || !ref.current) return;
        ref.current.innerHTML = svg;
        bindFunctions?.(ref.current);
      })
      .catch(() => setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [id, mode, source]);

  if (failed) return <pre className="diagram-source">{source}</pre>;
  return <div ref={ref} className="diagram-block" aria-label="Diagram" />;
}
