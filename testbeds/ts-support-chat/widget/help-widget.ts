// Embeddable help widget for customer sites (bundled by widget/build.mjs, no framework).
// It talks to our OpenAI proxy, which adds the real API key and rate limits per site.
import OpenAI from "openai";
import { marked } from "marked";

const client = new OpenAI({
  baseURL: `${location.origin}/api/openai-proxy/v1`,
  apiKey: "widget-session",
  dangerouslyAllowBrowser: true,
});

type Turn = { role: "user" | "assistant"; content: string };

const TRANSCRIPT_ID = "hw-transcript";

// Mirrors each answer into the printable transcript panel the site can show on request.
function saveTranscriptEntry(question: string, answerMarkdown: string): void {
  const panel = document.getElementById(TRANSCRIPT_ID);
  if (!panel) return;
  panel.insertAdjacentHTML(
    "beforeend",
    `<dt>${question.replace(/</g, "&lt;")}</dt><dd>${marked.parse(answerMarkdown)}</dd>`,
  );
}

export class HelpWidget {
  private readonly log: HTMLElement;
  private readonly status: HTMLElement;
  private readonly footer: HTMLElement;
  private readonly history: Turn[] = [];

  constructor(root: HTMLElement) {
    this.log = root.querySelector(".hw-log")!;
    this.status = root.querySelector(".hw-status")!;
    this.footer = root.querySelector(".hw-footer")!;
  }

  async ask(question: string): Promise<void> {
    this.addUserBubble(question);
    this.history.push({ role: "user", content: question });
    const bubble = this.addBubble("assistant");
    this.status.textContent = "Thinking…";

    const runner = client.chat.completions.stream({
      model: "gpt-4.1-mini",
      messages: [{ role: "system", content: "You answer questions about Example Cloud." }, ...this.history],
    });
    runner.on("content", (_delta, snapshot) => {
      bubble.innerHTML = marked.parseInline(snapshot) as string;
      this.log.scrollTop = this.log.scrollHeight;
    });

    const final = await runner.finalChatCompletion();
    const answer = final.choices[0].message.content ?? "";
    this.history.push({ role: "assistant", content: answer });
    saveTranscriptEntry(question, answer);
    this.status.textContent = "";
    this.footer.innerHTML = `<span class="hw-tokens">${final.usage?.total_tokens ?? 0} tokens</span>`;
  }

  private addUserBubble(text: string): void {
    const bubble = this.addBubble("user");
    bubble.textContent = text;
  }

  private addBubble(role: Turn["role"]): HTMLElement {
    const bubble = document.createElement("div");
    bubble.className = `hw-bubble hw-${role}`;
    this.log.append(bubble);
    return bubble;
  }
}
