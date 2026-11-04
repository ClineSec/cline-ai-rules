package com.example.opsdesk.handoff;

import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.service.AiServices;
import dev.langchain4j.service.MemoryId;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;
import java.time.LocalDate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/handoff")
public class ShiftHandoffController {

    /** Writes the end-of-shift handoff note. */
    interface HandoffWriter {

        @SystemMessage({
                "You write end-of-shift handoff notes for the {{team}} on-call team.",
                "Keep it under 200 words, list open incidents first, and use a {{tone}} tone."
        })
        String write(String team, @V("tone") String tone, @UserMessage String shiftLog);

        @SystemMessage("You summarize a shift for the incident review on {{day}}.")
        String review(@UserMessage String shiftLog, @V("day") LocalDate day);
    }

    /** Free-form chat about the current shift, one memory per engineer. */
    interface ShiftChat {
        String chat(@MemoryId String engineer, @UserMessage String message);
    }

    public record HandoffRequest(String team, String shiftLog) {}

    public record ChatRequest(String engineer, String site, String message) {}

    private final ChatModel model;
    private final HandoffWriter writer;

    public ShiftHandoffController(ChatModel langchainModel) {
        this.model = langchainModel;
        this.writer = AiServices.builder(HandoffWriter.class)
                .chatModel(langchainModel)
                .build();
    }

    @PostMapping("/note")
    public String note(@RequestBody HandoffRequest request) {
        return writer.write(request.team(), "matter-of-fact", request.shiftLog());
    }

    @PostMapping("/review")
    public String review(@RequestBody HandoffRequest request,
                         @RequestParam(required = false) LocalDate day) {
        return writer.review(request.shiftLog(), day != null ? day : LocalDate.now());
    }

    @PostMapping("/chat")
    public String chat(@RequestBody ChatRequest request) {
        ShiftChat chat = AiServices.builder(ShiftChat.class)
                .chatModel(model)
                .chatMemoryProvider(id -> MessageWindowChatMemory.withMaxMessages(20))
                .systemMessageProvider(id -> "You are the shift assistant for the "
                        + request.site() + " datacenter. Only discuss that site.")
                .build();
        return chat.chat(request.engineer(), request.message());
    }

    @GetMapping("/teams")
    public String teams() {
        return "network,storage,platform";
    }
}
