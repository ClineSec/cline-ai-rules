package com.example.fixtures;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.ai.chat.prompt.SystemPromptTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AssistController {

    private static final Map<String, String> PERSONAS = Map.of(
            "billing", "You are a careful billing assistant.",
            "tech", "You are a patient technical support agent.");

    enum Tone { FRIENDLY, FORMAL }

    record AskRequest(String persona, String question) {}

    private final ChatClient chatClient;

    AssistController(ChatClient.Builder builder) {
        this.chatClient = builder.build();
    }

    @GetMapping("/ask")
    public String ask(@RequestParam String persona, @RequestParam("q") String question) {
        return chatClient.prompt()
                // ruleid: user-input-in-system-prompt-java
                .system("You are " + persona + ". Answer briefly.")
                .user(question)
                .call()
                .content();
    }

    @PostMapping("/ask")
    public String askJson(@RequestBody AskRequest body) {
        return chatClient.prompt()
                .system(s -> s.text("Act as {persona}.")
                        // ruleid: user-input-in-system-prompt-java
                        .param("persona", body.persona()))
                .user(body.question())
                .call()
                .content();
    }

    @GetMapping("/tenant/{tenant}")
    public String tenant(@PathVariable String tenant, @RequestParam String q) {
        var template = new SystemPromptTemplate("You support the {tenant} workspace.");
        // ruleid: user-input-in-system-prompt-java
        var system = template.createMessage(Map.of("tenant", tenant));
        return chatClient.prompt(new Prompt(system, new org.springframework.ai.chat.messages.UserMessage(q))).call().content();
    }

    @GetMapping("/servlet")
    public String servlet(HttpServletRequest request) {
        String role = request.getParameter("role");
        // ruleid: user-input-in-system-prompt-java
        var system = new SystemMessage("The caller's role is " + role);
        return chatClient.prompt(new Prompt(system)).call().content();
    }

    // Near misses.

    @GetMapping("/persona")
    public String persona(@RequestParam String persona, @RequestParam String q) {
        // ok: user-input-in-system-prompt-java
        String system = PERSONAS.getOrDefault(persona, PERSONAS.get("billing"));
        return chatClient.prompt().system(system).user(q).call().content();
    }

    @GetMapping("/tone")
    public String tone(@RequestParam Tone tone, @RequestParam int maxWords, @RequestParam String q) {
        return chatClient.prompt()
                // ok: user-input-in-system-prompt-java
                .system("Use a " + tone + " tone in at most " + maxWords + " words.")
                .user(q)
                .call()
                .content();
    }

    @GetMapping("/user-turn")
    public String userTurn(@RequestParam String q) {
        return chatClient.prompt()
                .system("You are a support assistant.")
                // ok: user-input-in-system-prompt-java
                .user(u -> u.text("Customer asks: {q}").param("q", q))
                .call()
                .content();
    }

    @GetMapping("/length")
    public String length(@RequestParam String q) {
        return chatClient.prompt()
                // ok: user-input-in-system-prompt-java
                .system("The question is " + q.length() + " characters long.")
                .user(q)
                .call()
                .content();
    }
}
