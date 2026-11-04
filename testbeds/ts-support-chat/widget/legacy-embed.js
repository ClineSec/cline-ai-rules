// jQuery version of the help widget, still served to customer sites on the old CMS theme
// (which ships jQuery 3). Uses the same proxy as help-widget.ts.
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: `${location.origin}/api/openai-proxy/v1`,
  apiKey: "widget-session",
  dangerouslyAllowBrowser: true,
});

export function mountLegacyWidget(selector) {
  const $root = $(selector);
  const $log = $root.find(".hw-log");

  $root.on("submit", "form", async (event) => {
    event.preventDefault();
    const question = String($root.find("input[name=q]").val() || "");
    $log.append($("<div class='hw-bubble hw-user'></div>").text(question));

    const completion = await client.chat.completions.create({
      model: "gpt-4.1-mini",
      messages: [{ role: "user", content: question }],
    });
    const answer = completion.choices[0].message.content || "";
    $("<div class='hw-bubble hw-assistant'></div>").html(answer).appendTo($log);
    $root.find(".hw-footer").text(`${completion.usage?.total_tokens || 0} tokens`);
  });
}
