// Older "quick answer" card from before the TypeScript migration; still used on the
// help-center search page.
import { useEffect, useRef } from "react";
import { useCompletion } from "ai/react";
import { marked } from "marked";

export default function QuickAnswer({ question }) {
  const { completion, complete } = useCompletion({ api: "/api/draft" });
  const answerRef = useRef(null);

  useEffect(() => {
    if (question) complete(question);
  }, [question]);

  useEffect(() => {
    if (answerRef.current) {
      answerRef.current.innerHTML = marked(completion);
    }
  }, [completion]);

  return (
    <aside className="quick-answer">
      <h2>Quick answer</h2>
      <div ref={answerRef} />
    </aside>
  );
}
