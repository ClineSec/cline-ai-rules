package com.example.opsdesk.web;

import java.util.List;
import java.util.Map;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/runbooks")
public class RunbookController {

    private static final Map<String, String> PERSONAS = Map.of(
            "sre", "Answer like a senior SRE: short, precise, cite the runbook section.",
            "helpdesk", "Answer like a helpdesk lead: plain words, one step at a time.");

    private static final String TIER_TEMPLATE = """
            The caller is on the {tier} support tier for the {team} team.
            Only describe steps that tier is allowed to perform.
            """;

    private final ChatClient chatClient;

    public RunbookController(ChatClient opsChatClient) {
        this.chatClient = opsChatClient;
    }

    public record RunbookQuestion(String service, String question, List<String> runbookIds) {}

    public record RunbookAnswer(String service, String answer) {}

    /** Q&A over runbooks, scoped to the caller's team (from the gateway's headers). */
    @PostMapping("/ask")
    public RunbookAnswer ask(@RequestHeader("X-Ops-Team") String team,
                             @RequestHeader(value = "X-Ops-Tier", defaultValue = "l1") String tier,
                             @RequestBody RunbookQuestion body) {
        String answer = chatClient.prompt()
                .system(s -> s.text(TIER_TEMPLATE)
                        .param("team", team)
                        .param("tier", tier))
                .user(body.question())
                .call()
                .content();
        return new RunbookAnswer(body.service(), answer);
    }

    /** Same Q&A for the chat widget, which sends the service it was opened from. */
    @PostMapping("/widget")
    public RunbookAnswer widget(@RequestBody RunbookQuestion body) {
        String answer = chatClient.prompt()
                .system(scopeFor(body.service()))
                .user(body.question())
                .call()
                .content();
        return new RunbookAnswer(body.service(), answer);
    }

    /** Persona picked by the caller, but only from the fixed table. */
    @PostMapping("/persona")
    public RunbookAnswer persona(@RequestParam(defaultValue = "helpdesk") String persona,
                                 @RequestBody RunbookQuestion body) {
        String system = PERSONAS.getOrDefault(persona, PERSONAS.get("helpdesk"));
        String answer = chatClient.prompt()
                .system(system)
                .user(u -> u.text("Service: {service}\nQuestion: {question}")
                        .param("service", body.service())
                        .param("question", body.question()))
                .call()
                .content();
        return new RunbookAnswer(body.service(), answer);
    }

    /** One-paragraph summary of a runbook, linked from the on-call wiki. */
    @GetMapping("/{id}/summary")
    public String summary(@PathVariable String id) {
        return chatClient.prompt()
                .user("Summarize runbook " + id + " in one paragraph for the on-call wiki.")
                .call()
                .content();
    }

    /** The same summary for the CLI, as plain text. */
    @GetMapping(value = "/{id}/summary.txt", produces = MediaType.TEXT_PLAIN_VALUE)
    public String summaryText(@PathVariable String id) {
        return chatClient.prompt()
                .user("Summarize runbook " + id + " in one paragraph.")
                .call()
                .content();
    }

    /** The same summary for the dashboard, as JSON. */
    @GetMapping("/{id}/summary.json")
    public RunbookAnswer summaryJson(@PathVariable String id) {
        String answer = chatClient.prompt()
                .user("Summarize runbook " + id + " in one paragraph.")
                .call()
                .content();
        return new RunbookAnswer(id, answer);
    }

    private String scopeFor(String service) {
        return "You only answer questions about the " + service + " service. Refuse anything else.";
    }
}
