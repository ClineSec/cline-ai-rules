package com.example.fixtures;

import dev.langchain4j.data.message.SystemMessage;
import dev.langchain4j.data.message.UserMessage;
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.input.PromptTemplate;
import dev.langchain4j.service.AiServices;
import dev.langchain4j.service.MemoryId;
import dev.langchain4j.service.V;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ConciergeController {

    interface Concierge {
        @dev.langchain4j.service.SystemMessage("You are the {{brand}} concierge. Never discuss refunds.")
        String answer(@V("brand") String brand, @dev.langchain4j.service.UserMessage String question);

        @dev.langchain4j.service.SystemMessage("You write release notes for {{product}}.")
        String notes(@dev.langchain4j.service.UserMessage String changes, String product);

        @dev.langchain4j.service.SystemMessage("Answer the user's question about {{topic}}.")
        String explain(@dev.langchain4j.service.UserMessage String question, String topic);

        String chat(@MemoryId String sessionId, @dev.langchain4j.service.UserMessage String message);

        @dev.langchain4j.service.SystemMessage({
                "You draft escalation emails.",
                "Sign them as the {{desk}} desk."
        })
        String escalate(String desk, @dev.langchain4j.service.UserMessage String details);
    }

    @dev.langchain4j.service.SystemMessage("You triage tickets for the {{queue}} queue.")
    interface Triage {
        String route(String queue, @dev.langchain4j.service.UserMessage String ticket);
    }

    record TriageRequest(String queue, String ticket) {}

    private final ChatModel model;
    private final Concierge concierge;
    private final Triage triage;

    ConciergeController(ChatModel model) {
        this.model = model;
        this.concierge = AiServices.create(Concierge.class, model);
        this.triage = AiServices.create(Triage.class, model);
    }

    @GetMapping("/lc")
    public String langchain(@RequestHeader("X-Team") String team, @RequestParam String q) {
        // ruleid: user-input-in-system-prompt-java
        var system = SystemMessage.from("You help the " + team + " team.");
        return model.chat(system, UserMessage.from(q)).aiMessage().text();
    }

    @GetMapping("/provider")
    public String provider(@RequestParam String region, @RequestParam String q) {
        Concierge regional = AiServices.builder(Concierge.class)
                .chatModel(model)
                // ruleid: user-input-in-system-prompt-java
                .systemMessageProvider(memoryId -> "Answer for the " + region + " region.")
                .build();
        return regional.answer("acme", q);
    }

    @GetMapping("/template")
    public String template(@RequestParam String audience, @RequestParam String q) {
        // ruleid: user-input-in-system-prompt-java
        var system = PromptTemplate.from("Write for {{audience}}.").apply(Map.of("audience", audience)).toSystemMessage();
        return model.chat(system, UserMessage.from(q)).aiMessage().text();
    }

    @GetMapping("/brand")
    public String brand(@RequestParam String brand, @RequestParam String q) {
        // ruleid: user-input-in-system-prompt-java
        return concierge.answer(brand, q);
    }

    @GetMapping("/notes")
    public String notes(String product, String changes) {
        // ruleid: user-input-in-system-prompt-java
        return concierge.notes(changes, product);
    }

    @PostMapping("/triage")
    public String triage(@RequestBody TriageRequest request) {
        // ruleid: user-input-in-system-prompt-java
        return triage.route(request.queue(), request.ticket());
    }

    @GetMapping("/escalate")
    public String escalate(@RequestParam String desk, @RequestParam String details) {
        // ruleid: user-input-in-system-prompt-java
        return concierge.escalate(desk, details);
    }

    // Near misses.

    @GetMapping("/brand-question")
    public String brandQuestion(@RequestParam String q) {
        // ok: user-input-in-system-prompt-java
        return concierge.answer("acme", q);
    }

    @GetMapping("/changes")
    public String changes(@RequestParam String changes) {
        // ok: user-input-in-system-prompt-java
        return concierge.notes(changes, "Helpdesk");
    }

    @GetMapping("/explain")
    public String explain(@RequestParam String question) {
        // ok: user-input-in-system-prompt-java
        return concierge.explain(question, "billing");
    }

    @GetMapping("/chat")
    public String chat(@RequestHeader("X-Session") String session, @RequestParam String message) {
        // ok: user-input-in-system-prompt-java
        return concierge.chat(session, message);
    }

    @GetMapping("/user-message")
    public String userMessage(@RequestParam String q) {
        var system = SystemMessage.from("You are a support assistant.");
        // ok: user-input-in-system-prompt-java
        return model.chat(system, UserMessage.from("Customer asks: " + q)).aiMessage().text();
    }
}
