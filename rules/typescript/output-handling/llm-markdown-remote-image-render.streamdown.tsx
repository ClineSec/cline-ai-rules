// Streamdown with its rehype-harden image allowlist pinned to one CDN, in a plugin list that
// the module's renderers share.
import { Streamdown, defaultRehypePlugins } from "streamdown";
import { harden } from "rehype-harden";
import { useChat } from "@ai-sdk/react";

const PINNED_REHYPE = [
  defaultRehypePlugins.raw,
  defaultRehypePlugins.sanitize,
  [harden, { allowedImagePrefixes: ["https://cdn.example.com/"], allowedLinkPrefixes: ["*"] }],
];

export function PinnedThread() {
  const { messages } = useChat();
  return messages.map((message) =>
    message.parts.map((part, i) =>
      part.type === "text" ? (
        <Streamdown key={i} rehypePlugins={PINNED_REHYPE}>
          {/* ok: llm-markdown-remote-image-render */}
          {part.text}
        </Streamdown>
      ) : null,
    ),
  );
}
